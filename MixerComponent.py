# uncompyle6 version 3.4.1
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  2 2019, 14:32:10) 
# [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)]
# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/Launch_Control_XL/MixerComponent.py
# Compiled at: 2019-04-09 19:23:44

try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

import traceback
from _Framework.Control import control_list, ButtonControl, Control
from _Framework.Util import nop
from _Framework.Util import nop
from _Framework.ChannelStripComponent import ChannelStripComponent as ChannelStripComponentBase
from _Framework.MixerComponent import MixerComponent as MixerComponentBase
from .LedElement import LedElement
from .LedControl import LedControl
from _Framework.Util import clamp, nop
from ableton.v2.base import listens, listens_group, EventObject
from functools import partial
from .Constants import *
from .ChannelStripComponent import *

NUM_ROWS = 3

class MixerComponent(MixerComponentBase):
    def __init__(self, controller, num_tracks=0, num_returns=0, auto_name=False, invert_mute_feedback=False, *a, **k):
        self.controller = controller
        self._reset_led_colors()
        assert num_tracks >= 0
        assert num_returns >= 0
        super(MixerComponentBase, self).__init__(*a, **k)
        self._track_offset = -1
        self._send_index = 0
        self._bank_up_button = None
        self._bank_down_button = None
        self._next_track_button = None
        self._prev_track_button = None
        self._prehear_volume_control = None
        self._crossfader_control = None
        self._send_controls = None
        self._channel_strips = []
        self._return_strips = []
        self._offset_can_start_after_tracks = False

        for index in range(num_tracks):
            strip = self._create_strip("Track %d" % index)
            self._channel_strips.append(strip)
            self.register_components(self._channel_strips[index])
            if invert_mute_feedback:
                strip.set_invert_mute_feedback(True)

        for index in range(num_returns):
            self._return_strips.append(self._create_strip("Return %d" % index))
            self.register_components(self._return_strips[index])

        self._master_strip = self._create_strip("Master")
        self.register_components(self._master_strip)
        self._master_strip.set_track(self.song().master_track)
        self._selected_strip = self._create_strip("Selected")
        self.register_components(self._selected_strip)
        self.on_selected_track_changed()
        self.set_track_offset(0)
        if auto_name:
            self._auto_name()
        self._on_return_tracks_changed.subject = self.song()
        self._on_return_tracks_changed()

        def make_button_slot(name):
            return self.register_slot(None, getattr(self, '_%s_value' % name), 'value')

        self._bank_up_button_slot = make_button_slot('bank_up')
        self._bank_down_button_slot = make_button_slot('bank_down')
        self._next_track_button_slot = make_button_slot('next_track')
        self._prev_track_button_slot = make_button_slot('prev_track')
        return

    def on_selected_track_changed(self):
        selected_track = self.song().view.selected_track
        if self._selected_strip != None:
            self._selected_strip.set_track(selected_track)
        return

    @property
    def all_strips(self):
        return self._channel_strips + [self._master_strip]

    def _create_strip(self, user_friendly_name):
        if user_friendly_name == "Master":
            strip = MasterChannelStripComponent(self.controller, user_friendly_name=user_friendly_name)
        elif user_friendly_name == "Selected":
            strip = SelectedStripComponent(self.controller, user_friendly_name=user_friendly_name)
        else:
            strip = ChannelStripComponent(self.controller, user_friendly_name=user_friendly_name)
        return strip

    def set_volume_controls(self, controls):
        for strip, control in zip_longest(self._channel_strips, controls or []):
            strip.set_volume_control(control)

    def set_leds(self, leds):
        for strip, led in zip_longest(self.all_strips, leds or []):
            if strip is not None:
                strip.set_led_control(led)

    def set_master_encoders(self, controls):
        self._master_strip.set_send_controls(controls)
        self.update()

    def set_master_fader(self, control):
        self._master_strip.set_volume_control(control)
        self.update()

    def set_send_controls(self, controls):
        self._send_controls = controls
        for index, channel_strip in enumerate(self._channel_strips):
            if self.send_index is None:
                channel_strip.set_send_controls([None])
            else:
                send_controls = [controls.get_button(index, i) for i in range(NUM_ROWS)] if controls else [None]
                skipped_sends = [None for _ in range(self.send_index)]
                channel_strip.set_send_controls(skipped_sends + send_controls)

        self.update()

    def _set_all_led_colors(self, red, green, blue):
        self._send_led_colors((red, green, blue)*9)

    def _send_led_colors(self, colors):
        sysex = (0xF0,) + SYSEX_PRODUCT_ID + (SYSEX_COMMAND_SET_ALL_COLORS, )
        sysex += colors
        sysex += (0xF7,)

        self.controller.send_midi(sysex)

    def update_leds(self):
        colors = tuple([strip.get_led_rgb_index() for strip in self.all_strips])
        self._send_led_colors(colors)

    def _reset_led_colors(self):
        sysex = (0xF0, 0x30, 0xF7)
        self.controller.send_midi(sysex)

    def _reassign_tracks(self):
        self.controller.log_debug_message("reassigning tracks...")
        super(MixerComponent, self)._reassign_tracks()

        #if any(filter(lambda x: x.needs_led_update, self._channel_strips)):
        if self.all_strips:
            self.update_leds()

    def update(self):
        self.controller.log_message('Mixercomponent update called.')
        super(MixerComponent, self).update()

