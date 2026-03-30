# SpeechToText — Linux

Voxtral-powered speech-to-text desktop app for Ubuntu/Linux with system tray integration.

## Features

- **System tray app** — lives in the Ubuntu indicator area (like Diodon)
- **Record & transcribe** — one click to record, auto-transcribes when you stop
- **Auto type at cursor** — transcription is automatically pasted where your cursor is (configurable)
- **Auto copy to clipboard** — transcription is always copied to clipboard
- **Visual editor** — optional floating editor to view/edit transcription
- **API key management** — add/test/manage your Mistral API key from Settings
- **2-minute recording limit** — optimized for Mistral's free tier
- Dark modern UI

## Install

```bash
chmod +x install.sh
./install.sh
```

## Configuration

On first launch, you'll see only "🔑 Add API Key" in the tray menu. Click it to enter and test your Mistral API key.

Config is stored at `~/.config/speechtotext/config.json`.

## Usage

- Launch from the application menu or system tray
- Click the microphone button to record
- Click again to stop and transcribe
- Use **Copy** or **Type at Cursor** to use the text
- Open **Settings** to manage API key and auto-type behavior

## Requirements

- Ubuntu 22.04+
- Python 3.10+
- GStreamer, GTK 3, AyatanaAppIndicator3
- xdotool (for type-at-cursor)

## Other Platforms

- [macOS version](https://github.com/bouddahami/SpeechToText-macOS)
- [Windows version](https://github.com/bouddahami/SpeechToText-Windows)
