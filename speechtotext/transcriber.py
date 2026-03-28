"""Mistral Voxtral transcription API client."""

import requests
import os

MISTRAL_API_URL = 'https://api.mistral.ai/v1/audio/transcriptions'
MODEL = 'voxtral-mini-latest'
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB


def transcribe(audio_path, api_key):
    """Transcribe an audio file using Mistral Voxtral.

    Args:
        audio_path: Path to the audio file (WAV format)
        api_key: Mistral API key

    Returns:
        Transcribed text string

    Raises:
        Exception on API errors
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f'Audio file not found: {audio_path}')

    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        raise ValueError('Audio file is empty')
    if file_size > MAX_FILE_SIZE:
        raise ValueError('Audio file too large (max ~2 minutes)')

    with open(audio_path, 'rb') as f:
        response = requests.post(
            MISTRAL_API_URL,
            headers={'Authorization': f'Bearer {api_key}'},
            files={'file': ('recording.wav', f, 'audio/wav')},
            data={'model': MODEL},
            timeout=60
        )

    if response.status_code != 200:
        error_msg = response.text[:200] if response.text else 'Unknown error'
        raise Exception(f'Transcription failed ({response.status_code}): {error_msg}')

    result = response.json()
    return result.get('text', '').strip()
