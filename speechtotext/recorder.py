"""Audio recording using GStreamer."""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import tempfile
import os

Gst.init(None)


class AudioRecorder:
    """Records audio from the microphone and saves to a WAV file."""

    MAX_DURATION = 120  # seconds

    def __init__(self):
        self.pipeline = None
        self.recording = False
        self.duration = 0
        self.filepath = None
        self._timer_id = None
        self.on_duration_update = None
        self.on_max_reached = None

    def start(self, on_duration_update=None, on_max_reached=None):
        """Start recording audio."""
        self.on_duration_update = on_duration_update
        self.on_max_reached = on_max_reached

        # Create temp file for recording
        fd, self.filepath = tempfile.mkstemp(suffix='.wav')
        os.close(fd)

        # Build GStreamer pipeline
        pipeline_str = (
            'autoaudiosrc ! audioconvert ! audioresample ! '
            'audio/x-raw,rate=16000,channels=1,format=S16LE ! '
            f'wavenc ! filesink location={self.filepath}'
        )

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
        except GLib.Error:
            # Fallback: try pulsesrc explicitly
            pipeline_str = (
                'pulsesrc ! audioconvert ! audioresample ! '
                'audio/x-raw,rate=16000,channels=1,format=S16LE ! '
                f'wavenc ! filesink location={self.filepath}'
            )
            self.pipeline = Gst.parse_launch(pipeline_str)

        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            raise RuntimeError('Failed to start audio recording. Check microphone.')

        self.recording = True
        self.duration = 0

        # Start duration timer
        self._timer_id = GLib.timeout_add(1000, self._tick)

    def _tick(self):
        """Timer callback - runs every second."""
        if not self.recording:
            return False
        self.duration += 1
        if self.on_duration_update:
            self.on_duration_update(self.duration)
        if self.duration >= self.MAX_DURATION:
            if self.on_max_reached:
                GLib.idle_add(self.on_max_reached)
            return False
        return True


    def stop(self):
        """Stop recording and return the path to the WAV file."""
        self.recording = False

        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

        if self.pipeline:
            # Send EOS to properly close the WAV file
            self.pipeline.send_event(Gst.Event.new_eos())
            bus = self.pipeline.get_bus()
            # Wait up to 2 seconds for EOS
            bus.timed_pop_filtered(
                2 * Gst.SECOND,
                Gst.MessageType.EOS | Gst.MessageType.ERROR
            )
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

        return self.filepath

    def cleanup(self):
        """Remove temp recording file."""
        if self.filepath and os.path.exists(self.filepath):
            os.unlink(self.filepath)
            self.filepath = None

    def format_duration(self, seconds=None):
        """Format seconds as M:SS string."""
        if seconds is None:
            seconds = self.duration
        m = seconds // 60
        s = seconds % 60
        return f'{m}:{s:02d}'
