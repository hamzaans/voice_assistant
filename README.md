# Jarvis Voice Assistant

A voice-controlled AI assistant that uses Ollama for responses and supports natural conversation with wake word detection.

## Features

- Wake word detection ("Jarvis")
- Natural voice responses using Microsoft Edge TTS
- Streaming responses for faster interaction
- Interrupt capability
- 30-second conversation window
- Integration with Ollama AI

## Prerequisites

- Python 3.12+
- Ollama running locally
- Working microphone
- Working speakers

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-assistant.git
   cd voice-assistant
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make sure Ollama is running:
   ```bash
   systemctl status ollama
   ```

## Usage

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the assistant:
   ```bash
   python src/voice_assistant.py
   ```

3. Say "Jarvis" to wake up the assistant
4. Speak your command
5. Say "Jarvis" again to interrupt if needed

## License

MIT License

## Acknowledgments

- Ollama for AI backend
- Microsoft Edge TTS for voice synthesis
- Picovoice for wake word detection
