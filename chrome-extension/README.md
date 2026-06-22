# SpeechToText — Chrome Extension

Chrome extension version of [SpeechToText-Linux](https://github.com/yassirboudda/SpeechToText-Linux).

## Features

- Record from microphone (up to 2 minutes)
- Transcribe with **Mistral Voxtral** (`voxtral-mini-latest`)
- Copy to clipboard automatically
- Auto-type at cursor in the active tab (optional)
- Pre-configured Mistral API key (free tier)

## Install for testing (unpacked)

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select this folder: `SpeechToText-Chrome`
5. Click the extension icon, allow microphone access, and test recording

## Usage

1. Focus a text field on any page (optional, for auto-type)
2. Click the SpeechToText icon → **Start Recording**
3. Speak, then click **Stop & Transcribe**
4. Text appears in the popup and is copied to clipboard

## Files

- `background.js` — orchestration + Mistral API
- `offscreen.js` — MediaRecorder in offscreen document
- `popup.html/js` — main UI
