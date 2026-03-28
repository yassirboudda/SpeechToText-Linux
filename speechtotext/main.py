#!/usr/bin/env python3
"""SpeechToText - Voxtral-powered speech transcription, all inside the system tray."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gst', '1.0')

import sys
import signal
import json
import os
import threading
import subprocess

from gi.repository import Gtk, Gdk, GLib

try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3
    except (ValueError, ImportError):
        AppIndicator3 = None

from speechtotext.recorder import AudioRecorder
from speechtotext.transcriber import transcribe

CONFIG_DIR = os.path.expanduser('~/.config/speechtotext')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')


def load_config():
    """Load configuration from config file."""
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        default_config = {'mistral_api_key': ''}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)
        return default_config

    with open(CONFIG_FILE) as f:
        return json.load(f)


class SpeechToTextApp:
    """All-in-tray speech-to-text app. No separate window needed."""

    PREVIEW_LEN = 90

    def __init__(self, api_key, icon_path):
        self.api_key = api_key
        self.recorder = AudioRecorder()
        self.is_recording = False
        self.is_transcribing = False
        self.transcription = ''

        # Create indicator
        self.indicator = AppIndicator3.Indicator.new(
            'speechtotext',
            icon_path,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title('SpeechToText')

        self._build_menu()

    def _build_menu(self):
        """Build the indicator menu with all controls inline."""
        self.menu = Gtk.Menu()

        # ── Record / Stop toggle ──
        self.record_item = Gtk.MenuItem(label='🎙  Start Recording')
        self.record_item.connect('activate', self._on_record_toggle)
        self.menu.append(self.record_item)

        # Status line (non-clickable)
        self.status_item = Gtk.MenuItem(label='Ready')
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # ── Transcription text ──
        self.text_item = Gtk.MenuItem(label='No transcription yet')
        self.text_item.set_sensitive(False)
        self.menu.append(self.text_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # ── Action buttons ──
        self.copy_item = Gtk.MenuItem(label='📋  Copy to Clipboard')
        self.copy_item.connect('activate', self._on_copy)
        self.copy_item.set_sensitive(False)
        self.menu.append(self.copy_item)

        self.type_item = Gtk.MenuItem(label='⌨  Type at Cursor')
        self.type_item.connect('activate', self._on_type_at_cursor)
        self.type_item.set_sensitive(False)
        self.menu.append(self.type_item)

        self.delete_item = Gtk.MenuItem(label='🗑  Delete Transcription')
        self.delete_item.connect('activate', self._on_delete)
        self.delete_item.set_sensitive(False)
        self.menu.append(self.delete_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # ── Quit ──
        quit_item = Gtk.MenuItem(label='Quit')
        quit_item.connect('activate', lambda _: Gtk.main_quit())
        self.menu.append(quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    # ── UI state ──

    def _refresh_menu(self):
        """Update all menu item labels and sensitivity."""
        if self.is_recording:
            dur = self.recorder.format_duration()
            self.record_item.set_label(f'⏹  Stop Recording  ({dur})')
            self.status_item.set_label('Recording…')
            self.record_item.set_sensitive(True)
        elif self.is_transcribing:
            self.record_item.set_label('⏳  Transcribing…')
            self.status_item.set_label('Transcribing…')
            self.record_item.set_sensitive(False)
        else:
            self.record_item.set_label('🎙  Start Recording')
            self.record_item.set_sensitive(True)

        has_text = bool(self.transcription.strip())
        self.copy_item.set_sensitive(has_text)
        self.type_item.set_sensitive(has_text)
        self.delete_item.set_sensitive(has_text)

        if has_text:
            preview = self.transcription.replace('\n', ' ')
            if len(preview) > self.PREVIEW_LEN:
                preview = preview[:self.PREVIEW_LEN] + '…'
            self.text_item.set_label(preview)
        else:
            self.text_item.set_label('No transcription yet')

    # ── Recording ──

    def _on_record_toggle(self, _item):
        if self.is_transcribing:
            return
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        try:
            self.recorder.start(
                on_duration_update=self._on_duration_tick,
                on_max_reached=self._on_max_duration,
            )
            self.is_recording = True
            GLib.idle_add(self._refresh_menu)
        except Exception as e:
            self.status_item.set_label(f'Error: {e}')

    def _stop_recording(self):
        filepath = self.recorder.stop()
        self.is_recording = False

        if filepath:
            self.is_transcribing = True
            GLib.idle_add(self._refresh_menu)
            t = threading.Thread(target=self._transcribe_bg, args=(filepath,))
            t.daemon = True
            t.start()
        else:
            GLib.idle_add(self._refresh_menu)

    def _on_duration_tick(self, _seconds):
        GLib.idle_add(self._refresh_menu)

    def _on_max_duration(self):
        self._stop_recording()

    # ── Transcription ──

    def _transcribe_bg(self, filepath):
        try:
            text = transcribe(filepath, self.api_key)
            GLib.idle_add(self._on_transcribe_ok, text)
        except Exception as e:
            GLib.idle_add(self._on_transcribe_err, str(e))
        finally:
            self.recorder.cleanup()

    def _on_transcribe_ok(self, text):
        self.is_transcribing = False
        if text:
            if self.transcription.strip():
                self.transcription += '\n' + text
            else:
                self.transcription = text
            self.status_item.set_label('✓ Transcription complete')
        else:
            self.status_item.set_label('No speech detected')
        self._refresh_menu()

    def _on_transcribe_err(self, error):
        self.is_transcribing = False
        self.status_item.set_label(f'Error: {error}')
        self._refresh_menu()

    # ── Actions ──

    def _on_copy(self, _item):
        text = self.transcription.strip()
        if not text:
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        self.status_item.set_label('Copied to clipboard!')

    def _on_type_at_cursor(self, _item):
        """Copy text and paste it where the user's cursor is."""
        text = self.transcription.strip()
        if not text:
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        # Menu auto-closes on click; the previously-focused window regains focus.
        # Wait for that, then simulate Ctrl+V.
        GLib.timeout_add(700, self._do_paste)

    def _do_paste(self):
        try:
            subprocess.run(
                ['xdotool', 'key', '--clearmodifiers', 'ctrl+v'],
                timeout=5, check=False,
            )
        except FileNotFoundError:
            try:
                subprocess.run(
                    ['wtype', '-M', 'ctrl', '-k', 'v'],
                    timeout=5, check=False,
                )
            except FileNotFoundError:
                pass
        return False

    def _on_delete(self, _item):
        self.transcription = ''
        self.status_item.set_label('Transcription deleted')
        self._refresh_menu()


def main():
    """Main entry point."""
    config = load_config()

    api_key = config.get('mistral_api_key', '')
    if not api_key:
        print(f'Error: No Mistral API key configured.')
        print(f'Please set your API key in {CONFIG_FILE}')
        sys.exit(1)

    if AppIndicator3 is None:
        print('Error: AppIndicator3 required. Install gir1.2-ayatanaappindicator3-0.1')
        sys.exit(1)

    # Determine icon path
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets', 'icon.svg'
    )
    if not os.path.exists(icon_path):
        icon_path = os.path.expanduser(
            '~/.local/share/icons/hicolor/scalable/apps/speechtotext.svg'
        )
    if not os.path.exists(icon_path):
        icon_path = 'audio-input-microphone'

    SpeechToTextApp(api_key, icon_path)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()


if __name__ == '__main__':
    main()
