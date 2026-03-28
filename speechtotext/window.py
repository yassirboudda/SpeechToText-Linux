"""Main application window."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GLib, Pango
import threading
import subprocess
import os

from speechtotext.recorder import AudioRecorder
from speechtotext.transcriber import transcribe


class SpeechToTextWindow(Gtk.Window):
    """Main SpeechToText application window."""

    def __init__(self, api_key):
        super().__init__(title='SpeechToText')
        self.api_key = api_key
        self.recorder = AudioRecorder()
        self.is_recording = False
        self.is_transcribing = False
        self._placeholder_active = True

        # Window properties
        self.set_default_size(420, 540)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        self.set_decorated(True)

        # Don't destroy on close - just hide
        self.connect('delete-event', self._on_delete)

        # Set icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'assets', 'icon.svg'
        )
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)

        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.get_style_context().add_class('main-container')
        self.add(main_box)

        # ── Header ──
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_top(20)
        header_box.set_margin_start(20)
        header_box.set_margin_end(20)
        header_box.set_margin_bottom(12)

        # Icon circle
        icon_frame = Gtk.Frame()
        icon_frame.set_shadow_type(Gtk.ShadowType.NONE)
        icon_frame.get_style_context().add_class('icon-circle')
        icon_label = Gtk.Label(label='🎤')
        icon_label.set_size_request(44, 44)
        icon_frame.add(icon_label)
        header_box.pack_start(icon_frame, False, False, 0)

        # Title and subtitle
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_valign(Gtk.Align.CENTER)
        title = Gtk.Label(label='SpeechToText')
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class('header-title')
        title_box.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label='Voxtral-powered speech transcription')
        subtitle.set_halign(Gtk.Align.START)
        subtitle.get_style_context().add_class('header-subtitle')
        title_box.pack_start(subtitle, False, False, 0)

        header_box.pack_start(title_box, True, True, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_start(20)
        sep.set_margin_end(20)
        main_box.pack_start(sep, False, False, 0)

        # ── Recording section ──
        record_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        record_section.set_margin_top(24)
        record_section.set_margin_start(20)
        record_section.set_margin_end(20)
        record_section.set_halign(Gtk.Align.CENTER)

        # Record button
        self.record_btn = Gtk.Button()
        self.record_btn.set_size_request(80, 80)
        self.record_btn.get_style_context().add_class('record-button')
        self.record_btn.connect('clicked', self._on_record_clicked)

        self.record_btn_label = Gtk.Label(label='🎙')
        self.record_btn_label.modify_font(Pango.FontDescription('24'))
        self.record_btn.add(self.record_btn_label)

        record_section.pack_start(self.record_btn, False, False, 0)

        # Duration label
        self.duration_label = Gtk.Label(label='0:00')
        self.duration_label.get_style_context().add_class('duration-label')
        record_section.pack_start(self.duration_label, False, False, 0)

        # Status label
        self.status_label = Gtk.Label(label='Click to start recording')
        self.status_label.get_style_context().add_class('status-label')
        record_section.pack_start(self.status_label, False, False, 0)

        main_box.pack_start(record_section, False, False, 0)

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(16)
        sep2.set_margin_start(20)
        sep2.set_margin_end(20)
        main_box.pack_start(sep2, False, False, 0)

        # ── Output section ──
        output_label = Gtk.Label(label='Transcription Output')
        output_label.set_halign(Gtk.Align.START)
        output_label.set_margin_top(12)
        output_label.set_margin_start(20)
        output_label.get_style_context().add_class('section-label')
        main_box.pack_start(output_label, False, False, 0)

        # Text view in scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_margin_top(8)
        scroll.set_margin_start(20)
        scroll.set_margin_end(20)
        scroll.set_min_content_height(120)
        scroll.get_style_context().add_class('output-scroll')

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)
        self.text_view.get_style_context().add_class('output-text')

        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.set_text('Transcribed text will appear here...')
        self.text_buffer.connect('changed', self._on_buffer_changed)

        scroll.add(self.text_view)
        main_box.pack_start(scroll, True, True, 0)

        # ── Action buttons ──
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(12)
        btn_box.set_margin_start(20)
        btn_box.set_margin_end(20)
        btn_box.set_margin_bottom(20)
        btn_box.set_homogeneous(True)

        # Copy button
        self.copy_btn = Gtk.Button(label='📋  Copy')
        self.copy_btn.get_style_context().add_class('action-button')
        self.copy_btn.connect('clicked', self._on_copy_clicked)
        btn_box.pack_start(self.copy_btn, True, True, 0)

        # Type at cursor button
        self.type_btn = Gtk.Button(label='⌨  Type at Cursor')
        self.type_btn.get_style_context().add_class('type-button')
        self.type_btn.connect('clicked', self._on_type_clicked)
        btn_box.pack_start(self.type_btn, True, True, 0)

        main_box.pack_start(btn_box, False, False, 0)

    # ── Window control ──

    def _on_delete(self, widget, event):
        """Hide instead of destroy."""
        self.hide()
        return True

    def toggle_visibility(self):
        """Show or hide the window."""
        if self.get_visible():
            self.hide()
        else:
            self.show_all()
            self.present()

    def quick_record(self):
        """Show window and start recording immediately."""
        if not self.get_visible():
            self.show_all()
            self.present()
        if not self.is_recording and not self.is_transcribing:
            GLib.idle_add(self._start_recording)

    # ── Recording control ──

    def _on_record_clicked(self, button):
        """Toggle recording."""
        if self.is_transcribing:
            return
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start audio recording."""
        try:
            self.recorder.start(
                on_duration_update=self._update_duration,
                on_max_reached=self._on_max_duration
            )
            self.is_recording = True
            self._update_record_ui()
        except Exception as e:
            self.status_label.set_text(f'Error: {e}')

    def _stop_recording(self):
        """Stop recording and start transcription."""
        filepath = self.recorder.stop()
        self.is_recording = False

        if filepath:
            self.is_transcribing = True
            self._update_record_ui()
            # Transcribe in background
            thread = threading.Thread(
                target=self._transcribe_async, args=(filepath,)
            )
            thread.daemon = True
            thread.start()
        else:
            self._update_record_ui()

    def _on_max_duration(self):
        """Called when max recording duration is reached."""
        self._stop_recording()

    def _update_duration(self, seconds):
        """Update duration display."""
        GLib.idle_add(
            self.duration_label.set_text,
            self.recorder.format_duration(seconds)
        )

    # ── Transcription ──

    def _transcribe_async(self, filepath):
        """Transcribe audio in background thread."""
        try:
            text = transcribe(filepath, self.api_key)
            GLib.idle_add(self._on_transcription_done, text)
        except Exception as e:
            GLib.idle_add(self._on_transcription_error, str(e))
        finally:
            self.recorder.cleanup()

    def _on_transcription_done(self, text):
        """Called when transcription succeeds."""
        self.is_transcribing = False
        if text:
            start = self.text_buffer.get_start_iter()
            end = self.text_buffer.get_end_iter()
            existing = self.text_buffer.get_text(start, end, False)

            if self._placeholder_active:
                self.text_buffer.set_text(text)
                self._placeholder_active = False
            elif existing.strip():
                self.text_buffer.set_text(f'{existing}\n{text}')
            else:
                self.text_buffer.set_text(text)

            self.status_label.set_text('Transcription complete')
        else:
            self.status_label.set_text('No speech detected')
        self._update_record_ui()

    def _on_transcription_error(self, error):
        """Called when transcription fails."""
        self.is_transcribing = False
        self.status_label.set_text(f'Error: {error}')
        self._update_record_ui()

    def _on_buffer_changed(self, buffer):
        """Track when user manually edits text."""
        if self._placeholder_active:
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            text = buffer.get_text(start, end, False)
            if text != 'Transcribed text will appear here...':
                self._placeholder_active = False

    # ── UI state ──

    def _update_record_ui(self):
        """Update recording UI state."""
        ctx = self.record_btn.get_style_context()

        if self.is_transcribing:
            self.record_btn_label.set_text('⏳')
            self.record_btn.set_sensitive(False)
            ctx.remove_class('recording')
            ctx.add_class('transcribing')
            self.status_label.set_text('Transcribing...')
        elif self.is_recording:
            self.record_btn_label.set_text('⏹')
            self.record_btn.set_sensitive(True)
            ctx.remove_class('transcribing')
            ctx.add_class('recording')
            self.status_label.set_text('Recording... click to stop')
        else:
            self.record_btn_label.set_text('🎙')
            self.record_btn.set_sensitive(True)
            ctx.remove_class('recording')
            ctx.remove_class('transcribing')
            self.duration_label.set_text('0:00')
            current = self.status_label.get_text()
            keep = ('Transcription complete', 'No speech detected', 'Copied to clipboard!')
            if not current.startswith('Error') and current not in keep:
                self.status_label.set_text('Click to start recording')

    # ── Actions ──

    def _get_output_text(self):
        """Get text from the output buffer."""
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        text = self.text_buffer.get_text(start, end, False)
        if self._placeholder_active:
            return ''
        return text.strip()

    def _on_copy_clicked(self, button):
        """Copy transcription to clipboard."""
        text = self._get_output_text()
        if text:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            clipboard.store()
            self.status_label.set_text('Copied to clipboard!')
        else:
            self.status_label.set_text('Nothing to copy')

    def _on_type_clicked(self, button):
        """Type transcription at current cursor position."""
        text = self._get_output_text()
        if not text:
            self.status_label.set_text('Nothing to type')
            return

        # Copy to clipboard
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()

        # Hide window, then paste after a short delay
        self.hide()
        GLib.timeout_add(500, self._do_paste)

    def _do_paste(self):
        """Simulate Ctrl+V paste using xdotool."""
        try:
            subprocess.run(
                ['xdotool', 'key', '--clearmodifiers', 'ctrl+v'],
                timeout=5, check=False
            )
        except FileNotFoundError:
            # xdotool not found, try wtype for Wayland
            try:
                subprocess.run(
                    ['wtype', '-M', 'ctrl', '-k', 'v'],
                    timeout=5, check=False
                )
            except FileNotFoundError:
                pass
        return False
