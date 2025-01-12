import requests
import pvporcupine
import pyaudio
import struct
import speech_recognition as sr
import asyncio
import edge_tts
import pygame
import tempfile
import os
import logging
import time
import json
import aiohttp

# Create logs directory in user's home
log_dir = os.path.expanduser('~/voice_assistant/logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'voice-assistant.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)

async def get_ollama_response_stream(prompt, model="llama3"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response.raise_for_status()
                current_sentence = ""
                
                async for line in response.content:
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    if "response" in data:
                        current_sentence += data["response"]
                        
                        # When we hit sentence endings, yield the sentence
                        if any(current_sentence.rstrip().endswith(x) for x in ['.', '!', '?', ':', ';']):
                            yield current_sentence.strip()
                            current_sentence = ""
                
                # Yield any remaining text
                if current_sentence.strip():
                    yield current_sentence.strip()
                    
    except Exception as e:
        yield f"Error connecting to Ollama: {str(e)}"

class VoiceAssistant:
    def __init__(self):
        logging.info("Initializing Voice Assistant...")
        # Initialize wake word detection with just 'jarvis'
        self.porcupine = pvporcupine.create(
            access_key='vhFdaQtEDBCkXreqFhf1XmD6s1Z0t4SjwYAZpbkEKQ6NoDmvit2UQg==',
            keywords=['jarvis']  # Just use jarvis
        )
        
        # No need to track keyword since we only have one
        self.last_keyword = None
        
        # Initialize audio input for wake word
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # Select voice
        self.voice = "en-GB-RyanNeural"  # British male voice
        
        # Create temp directory for audio files
        self.temp_dir = tempfile.mkdtemp()
        
    async def speak(self, text):
        logging.info(f"Speaking: {text}")
        try:
            temp_file = os.path.join(self.temp_dir, "temp_audio.mp3")
            
            # Generate speech
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(temp_file)
            
            # Play audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # While speaking, also listen for interrupt command
            interrupted = False
            while pygame.mixer.music.get_busy() and not interrupted:
                for _ in range(10):  # Check wake word more frequently
                    if self.listen_for_wake_word():
                        pygame.mixer.music.stop()
                        logging.info("Speech interrupted by Jarvis command")
                        print("\nSpeech interrupted.")
                        interrupted = True
                        break
                    pygame.time.Clock().tick(10)
                
        finally:
            try:
                os.remove(temp_file)
            except:
                pass
            
        return interrupted
    
    def listen_for_wake_word(self):
        """Listen for wake word and return True if detected"""
        pcm = self.audio_stream.read(self.porcupine.frame_length)
        pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
        
        keyword_index = self.porcupine.process(pcm)
        return keyword_index >= 0
    
    def listen_for_command(self):
        logging.info("Listening for command...")
        with sr.Microphone() as source:
            try:
                logging.debug("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logging.debug("Listening for audio...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                logging.debug("Processing audio...")
                
                text = self.recognizer.recognize_google(audio)
                logging.info(f"Recognized text: {text}")
                return text
                
            except sr.WaitTimeoutError:
                logging.warning("No speech detected")
                return None
            except sr.UnknownValueError:
                logging.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logging.error(f"Could not request results: {e}")
                return None
            except Exception as e:
                logging.error(f"Unexpected error: {e}", exc_info=True)
                return None
    
    async def run(self):
        print("Voice Assistant Ready! (Say 'Jarvis' to wake me up)")
        
        try:
            while True:
                if self.listen_for_wake_word():
                    await self.speak("At your service, sir")
                    
                    conversation_start = time.time()
                    last_interaction = time.time()
                    
                    while True:
                        if time.time() - last_interaction > 30:
                            logging.info("Conversation timed out after 30 seconds of inactivity")
                            await self.speak("Standing by")
                            break
                        
                        command = self.listen_for_command()
                        if command:
                            last_interaction = time.time()
                            print("\nAssistant: ", end='', flush=True)
                            
                            # Stream the response sentence by sentence
                            async for sentence in get_ollama_response_stream(command):
                                print(sentence, end=' ', flush=True)
                                if await self.speak(sentence):  # If interrupted
                                    break
                            
                            print()  # New line after complete response
                            
                        elif time.time() - last_interaction > 10:
                            print("Listening for follow-up...")
        
        except KeyboardInterrupt:
            print("\nStopping voice assistant...")
        
        finally:
            self.audio_stream.close() 
            self.pa.terminate()
            self.porcupine.delete()
            try:
                os.rmdir(self.temp_dir)
            except:
                pass

def main():
    assistant = VoiceAssistant()
    asyncio.run(assistant.run())

if __name__ == "__main__":
    main() 