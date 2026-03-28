"""Visual editor window — optional companion to the tray menu."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GLib, Pango
import subprocess
import os


class EditorWindow(Gtk.Window):
    """Floating editor for viewing / editing transcription text."""

    def __init__(self, app):
        super().__init__(title='SpeechToText — Editor')
        self.app = app
        self._internal_update = False

        # Window properties
        self.set_default_size(420, 400)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)

        # Load CSS
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
        if os.path.exists(css_path):
            css_provider = Gtk.CssProvider()
            css_provider.load_from_path(css_path)
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        # Set dark theme
        settings = Gtk.Settings.get_default()
        settings.set_property('gtk-application-prefer-dark-theme', True)

        # Icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'assets', 'icon.svg'
        )
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)

        # Hide instead of destroy
        self.connect('delete-event', self._on_delete)

        self._build_ui()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.get_style_context().add_class('main-container')
        self.add(main_box)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_top(16)
        header_box.set_margin_start(20)
        header_box.set_margin_end(20)
        header_box.set_margin_bottom(12)

        icon_frame = Gtk.Frame()
        icon_frame.set_shadow_type(Gtk.ShadowType.NONE)
        icon_frame.get_style_context().add_class('icon-circle')
        icon_label = Gtk.Label(label='🎤')
        icon_label.set_size_request(36, 36)
        icon_frame.add(icon_label)
        header_box.pack_start(icon_frame, False, False, 0)

        title = Gtk.Label(label='Transcription Editor')
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class('header-title')
        header_box.pack_start(title, True, True, 0)

        main_box.pack_start(header_box, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_start(20)
        sep.set_margin_end(20)
        main_box.pack_start(sep, False, False, 0)

        # Editable text area
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_margin_top(12)
        scroll.set_margin_start(20)
        scroll.set_margin_end(20)
        scroll.set_min_content_height(180)
        scroll.get_style_context().add_class('output-scroll')

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)
        self.text_view.get_style_context().add_class('output-text')

        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.connect('changed', self._on_buffer_changed)

        scroll.add(self.text_view)
        main_box.pack_start(scroll, True, True, 0)

        # Status
        self.status_label = Gtk.Label(label='Edit transcription text above')
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_margin_top(6)
        self.status_label.set_margin_start(20)
        self.status_label.get_style_context().add_class('status-label')
        main_box.pack_start(self.status_label, False, False, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(10)
        btn_box.set_margin_start(20)
        btn_box.set_margin_end(20)
        btn_box.set_margin_bottom(16)
        btn_box.set_homogeneous(True)

        copy_btn = Gtk.Button(label='📋  Copy')
        copy_btn.get_style_context().add_class('action-button')
        copy_btn.connect('clicked', self._on_copy)
        btn_box.pack_start(copy_btn, True, True, 0)

        type_btn = Gtk.Button(label='⌨  Type at Cursor')
        type_btn.get_style_context().add_class('type-button')
        type_btn.connect('clicked', self._on_type)
        btn_box.pack_start(type_btn, True, True, 0)

        delete_btn = Gtk.Button(label='🗑  Delete')
        delete_btn.get_style_context().add_class('delete-button')
        delete_btn.connect('clicked', self._on_clear)
        btn_box.pack_start(delete_btn, True, True, 0)

        main_box.pack_start(btn_box, False, False, 0)

    # ── Public ──

    def set_text(self, text):
        """Set the text from the tray app without triggering sync-back."""
        self._internal_update = True
        self.text_buffer.set_text(text or '')
        self._internal_update = False

    def get_text(self):
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        return self.text_buffer.get_text(start, end, False).strip()

    # ── Callbacks ──

    def _on_delete(self, widget, event):
        self.hide()
        return True

    def _on_buffer_changed(self, buffer):
        if self._internal_update:
            return
        self.app.update_transcription_from_editor(self.get_text())

    def _on_copy(self, _btn):
        text = self.get_text()
        if text:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            clipboard.store()
            self.status_label.set_text('Copied to clipboard!')
        else:
            self.status_label.set_text('Nothing to copy')

    def _on_type(self, _btn):
        text = self.get_text()
        if not text:
            self.status_label.set_text('Nothing to type')
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        self.hide()
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

    def _on_clear(self, _btn):
        self.text_buffer.set_text('')
        self.app.update_transcription_from_editor('')
        self.status_label.set_text('Transcription deleted')
