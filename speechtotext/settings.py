"""Settings window — API key management and preferences."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GLib
import os
import threading


class SettingsWindow(Gtk.Window):
    """Settings dialog with API key management and behavior toggles."""

    def __init__(self, app):
        super().__init__(title='SpeechToText — Settings')
        self.app = app
        self._key_tested = False
        self._testing = False

        # Window properties
        self.set_default_size(460, 340)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
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

        # Dark theme
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

        # ── Header ──
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_top(16)
        header_box.set_margin_start(20)
        header_box.set_margin_end(20)
        header_box.set_margin_bottom(12)

        icon_frame = Gtk.Frame()
        icon_frame.set_shadow_type(Gtk.ShadowType.NONE)
        icon_frame.get_style_context().add_class('icon-circle')
        icon_label = Gtk.Label(label='⚙')
        icon_label.set_size_request(36, 36)
        icon_frame.add(icon_label)
        header_box.pack_start(icon_frame, False, False, 0)

        title = Gtk.Label(label='Settings')
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class('header-title')
        header_box.pack_start(title, True, True, 0)

        main_box.pack_start(header_box, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_start(20)
        sep.set_margin_end(20)
        main_box.pack_start(sep, False, False, 0)

        # ── API Key section ──
        key_label = Gtk.Label(label='Mistral API Key')
        key_label.set_halign(Gtk.Align.START)
        key_label.set_margin_top(16)
        key_label.set_margin_start(20)
        key_label.get_style_context().add_class('section-label')
        main_box.pack_start(key_label, False, False, 0)

        key_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        key_row.set_margin_top(6)
        key_row.set_margin_start(20)
        key_row.set_margin_end(20)

        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text('Enter your Mistral API key…')
        self.key_entry.set_visibility(False)
        self.key_entry.get_style_context().add_class('settings-entry')
        self.key_entry.connect('changed', self._on_key_changed)
        key_row.pack_start(self.key_entry, True, True, 0)

        self.show_key_btn = Gtk.ToggleButton(label='👁')
        self.show_key_btn.get_style_context().add_class('settings-icon-btn')
        self.show_key_btn.connect('toggled', self._on_toggle_visibility)
        key_row.pack_start(self.show_key_btn, False, False, 0)

        main_box.pack_start(key_row, False, False, 0)

        # Test row
        test_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        test_row.set_margin_top(8)
        test_row.set_margin_start(20)
        test_row.set_margin_end(20)

        self.test_btn = Gtk.Button(label='🔍  Test Key')
        self.test_btn.get_style_context().add_class('action-button')
        self.test_btn.connect('clicked', self._on_test_key)
        test_row.pack_start(self.test_btn, False, False, 0)

        self.test_status = Gtk.Label(label='')
        self.test_status.set_halign(Gtk.Align.START)
        self.test_status.get_style_context().add_class('status-label')
        test_row.pack_start(self.test_status, True, True, 0)

        main_box.pack_start(test_row, False, False, 0)

        # ── Separator ──
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(16)
        sep2.set_margin_start(20)
        sep2.set_margin_end(20)
        main_box.pack_start(sep2, False, False, 0)

        # ── Behavior section ──
        beh_label = Gtk.Label(label='Behavior')
        beh_label.set_halign(Gtk.Align.START)
        beh_label.set_margin_top(12)
        beh_label.set_margin_start(20)
        beh_label.get_style_context().add_class('section-label')
        main_box.pack_start(beh_label, False, False, 0)

        auto_type_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        auto_type_row.set_margin_top(8)
        auto_type_row.set_margin_start(20)
        auto_type_row.set_margin_end(20)

        auto_type_label = Gtk.Label(label='Auto "Type at Cursor" after transcription')
        auto_type_label.set_halign(Gtk.Align.START)
        auto_type_label.get_style_context().add_class('settings-label')
        auto_type_row.pack_start(auto_type_label, True, True, 0)

        self.auto_type_switch = Gtk.Switch()
        self.auto_type_switch.get_style_context().add_class('settings-switch')
        auto_type_row.pack_start(self.auto_type_switch, False, False, 0)

        main_box.pack_start(auto_type_row, False, False, 0)

        # Spacer
        main_box.pack_start(Gtk.Box(), True, True, 0)

        # ── Save / Close buttons ──
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(10)
        btn_box.set_margin_start(20)
        btn_box.set_margin_end(20)
        btn_box.set_margin_bottom(16)

        close_btn = Gtk.Button(label='Cancel')
        close_btn.get_style_context().add_class('action-button')
        close_btn.connect('clicked', lambda _: self.hide())
        btn_box.pack_start(close_btn, True, True, 0)

        self.save_btn = Gtk.Button(label='💾  Save')
        self.save_btn.get_style_context().add_class('type-button')
        self.save_btn.connect('clicked', self._on_save)
        btn_box.pack_start(self.save_btn, True, True, 0)

        main_box.pack_start(btn_box, False, False, 0)

    # ── Public ──

    def refresh(self):
        """Reload values from the app before showing."""
        self.key_entry.set_text(self.app.api_key or '')
        self.auto_type_switch.set_active(self.app.auto_type)
        self._key_tested = bool(self.app.api_key)
        self._update_save_sensitivity()
        self.test_status.set_text('')

    # ── Callbacks ──

    def _on_delete(self, widget, event):
        self.hide()
        return True

    def _on_key_changed(self, entry):
        self._key_tested = False
        self._update_save_sensitivity()
        self.test_status.set_text('')

    def _on_toggle_visibility(self, btn):
        self.key_entry.set_visibility(btn.get_active())

    def _on_test_key(self, _btn):
        key = self.key_entry.get_text().strip()
        if not key:
            self.test_status.set_text('Please enter an API key first')
            return
        if self._testing:
            return
        self._testing = True
        self.test_btn.set_sensitive(False)
        self.test_status.set_text('Testing…')
        t = threading.Thread(target=self._test_key_bg, args=(key,))
        t.daemon = True
        t.start()

    def _test_key_bg(self, key):
        from speechtotext.transcriber import test_api_key
        ok, error = test_api_key(key)
        GLib.idle_add(self._on_test_result, ok, error)

    def _on_test_result(self, ok, error):
        self._testing = False
        self.test_btn.set_sensitive(True)
        if ok:
            self._key_tested = True
            self.test_status.set_text('✓ API key is valid')
        else:
            self._key_tested = False
            self.test_status.set_text(f'✗ {error}')
        self._update_save_sensitivity()

    def _update_save_sensitivity(self):
        key = self.key_entry.get_text().strip()
        # Allow save if: key tested valid, OR key is empty (to remove key)
        can_save = self._key_tested or not key
        self.save_btn.set_sensitive(can_save)

    def _on_save(self, _btn):
        new_key = self.key_entry.get_text().strip()
        new_auto_type = self.auto_type_switch.get_active()
        self.app.apply_settings(new_key, new_auto_type)
        self.hide()
