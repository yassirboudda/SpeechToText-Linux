# SpeechToText

Voxtral-powered speech-to-text desktop app for Ubuntu with system tray integration.

## Features

- **Record** audio from your microphone
- **Transcribe** using Mistral's Voxtral speech-to-text model
- **Copy** transcription to clipboard
- **Type at cursor** — paste transcribed text wherever your mouse is
- **System tray** indicator for quick access (like Diodon)
- Dark modern UI

## Install

```bash
chmod +x install.sh
./install.sh
```

## Configuration

Set your Mistral API key in `~/.config/speechtotext/config.json`:

```json
{
  "mistral_api_key": "your-key-here"
}
```

## Usage

- Launch from the application menu or system tray
- Click the microphone button to record
- Click again to stop and transcribe
- Use **Copy** or **Type at Cursor** to use the text

## Requirements

- Ubuntu 22.04+
- Python 3.10+
- GStreamer, GTK 3, AyatanaAppIndicator3
- xdotool (for type-at-cursor)
