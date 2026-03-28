#!/usr/bin/env python3
"""SpeechToText - Voxtral-powered speech transcription with system tray integration."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gst', '1.0')

import sys
import signal
import json
import os

from gi.repository import Gtk, Gdk, GLib

# Try Ayatana AppIndicator first (modern Ubuntu 22.04+), fall back to legacy
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3
    except (ValueError, ImportError):
        AppIndicator3 = None

from speechtotext.window import SpeechToTextWindow

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


def create_indicator(window, icon_path):
    """Create system tray indicator."""
    if AppIndicator3 is None:
        return None

    indicator = AppIndicator3.Indicator.new(
        'speechtotext',
        icon_path,
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_title('SpeechToText')

    menu = Gtk.Menu()

    # Show/Hide
    item_show = Gtk.MenuItem(label='Open SpeechToText')
    item_show.connect('activate', lambda _: window.toggle_visibility())
    menu.append(item_show)

    menu.append(Gtk.SeparatorMenuItem())

    # Quick Record
    item_record = Gtk.MenuItem(label='Quick Record')
    item_record.connect('activate', lambda _: window.quick_record())
    menu.append(item_record)

    menu.append(Gtk.SeparatorMenuItem())

    # Quit
    item_quit = Gtk.MenuItem(label='Quit')
    item_quit.connect('activate', lambda _: Gtk.main_quit())
    menu.append(item_quit)

    menu.show_all()
    indicator.set_menu(menu)

    return indicator


def main():
    """Main entry point."""
    # Load config
    config = load_config()

    api_key = config.get('mistral_api_key', '')
    if not api_key:
        print(f'Error: No Mistral API key configured.')
        print(f'Please set your API key in {CONFIG_FILE}')
        sys.exit(1)

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

    # Create window
    window = SpeechToTextWindow(api_key)

    # Determine icon path
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets', 'icon.svg'
    )
    if not os.path.exists(icon_path):
        icon_path = 'audio-input-microphone'

    # Create system tray indicator
    indicator = create_indicator(window, icon_path)

    if indicator is None:
        # No indicator support - just show the window
        window.show_all()

    # Handle SIGINT gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    Gtk.main()


if __name__ == '__main__':
    main()
