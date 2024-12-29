# uncompyle6 version 3.4.1
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  2 2019, 14:32:10) 
# [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)]
# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/Launch_Control_XL/KNTRL9.py
# Compiled at: 2019-04-09 19:23:44

from functools import partial
from itertools import chain
import Live
import inspect
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.EncoderElement import EncoderElement
from _Framework.SliderElement import SliderElement
from _Framework.SysexValueControl import SysexValueControl
from _Framework.IdentifiableControlSurface import IdentifiableControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE, MIDI_NOTE_TYPE, InputControlElement
from _Framework.Layer import Layer
from _Framework.ModesComponent import ModeButtonBehaviour, ModesComponent, AddLayerMode
from _Framework.SessionComponent import SessionComponent
from _Framework.SubjectSlot import subject_slot
from _Framework.Util import nop, BooleanContext, first, find_if, const, in_range
from _Framework import Task
from .ButtonElement import ButtonElement
from .DeviceComponent import DeviceComponent, DeviceModeComponent
from .MixerComponent import MixerComponent
from .LedMatrixElement import LedMatrixElement
from .LedElement import LedElement
from .Constants import *

class KNTRL9(IdentifiableControlSurface):
    def __init__(self, c_instance, *a, **k):
        super(KNTRL9, self).__init__(c_instance=c_instance, product_id_bytes=SYSEX_PRODUCT_ID, *a, **k)

        with self.component_guard():
            self._create_controls()
        self._initialize_task = self._tasks.add(Task.sequence(Task.wait(1), Task.run(self._create_components)))
        self._initialize_task.kill()

    def on_identified(self):
        self.log_message("Identified...")
        self._send_live_template()

    def _create_components(self):
        self._initialize_task.kill()
        self._disconnect_and_unregister_all_components()
        with self.component_guard():
            mixer = self._create_mixer()
            session = self._create_session()
            session.set_mixer(mixer)

        self.mixer = mixer

    def build_midi_map(self, midi_map_handle):
        """ Live -> Script
            Build DeviceParameter Mappings, that are processed in Audio time, or
            forward MIDI messages explicitly to our receive_midi_functions.
            Which means that when you are not forwarding MIDI, nor mapping parameters,
            you will never get any MIDI messages at all.
        """
        with self._in_build_midi_map():
            self._forwarding_registry.clear()
            self._forwarding_long_identifier_registry.clear()
            for control in self.controls:
                if isinstance(control, InputControlElement):
                    # install_connections(install_translation, install_mapping, install_forwarding):
                    # install_translation: the method that translates midi messages
                    # install_mapping: the method to install midi mapping
                    control.install_connections(self._translate_message, partial(self._install_mapping, midi_map_handle), partial(self._install_forwarding, midi_map_handle))

            if self._pad_translations is not None:
                self._c_instance.set_pad_translation(self._pad_translations)
        return


    def _create_controls(self):
        def make_led(identifier, name):
            return LedElement(self, midi_channel=LIVE_CHANNEL, index=identifier, name=name)

        def make_leds(identifiers, name):
            return [make_led(identifier, name % (i + 1)) for i, identifier in enumerate(identifiers)]

        def make_button(identifier, name, midi_type=MIDI_CC_TYPE):
            return ButtonElement(is_momentary=True, msg_type=midi_type, channel=LIVE_CHANNEL, identifier=identifier,
                                 name=name)

        def make_encoder(identifier, name):
            return EncoderElement(MIDI_CC_TYPE, LIVE_CHANNEL, identifier, name=name, map_mode=Live.MidiMap.MapMode.absolute_14_bit)

        def make_slider(identifier, name):
            return EncoderElement(MIDI_CC_TYPE, LIVE_CHANNEL, identifier, name=name, map_mode=Live.MidiMap.MapMode.absolute_14_bit, encoder_sensitivity=168)

        self._send_encoders = ButtonMatrixElement(
            rows=[
                [make_encoder(i, 'Top_Send_%d' % (i + 1)) for i in range(NUM_TRACKS)],
                [make_encoder(i + 9, 'Middle_Send_%d' % (i + 1)) for i in range(NUM_TRACKS)],
                [make_encoder(i + 18, 'Bottom_Send_%d' % (i + 1)) for i in range(NUM_TRACKS)],
            ])

        self._volume_faders = ButtonMatrixElement(rows=[[make_slider(i, 'Fader_%d' % (i - 26)) for i in [27, 28, 29, 30, 31, 64, 65, 66]]])

        self._master_fader = make_slider(67, "Master_Fader")
        self._master_encoders = ButtonMatrixElement(rows=[[make_encoder(i, "Master_Knob_%d" % (i / 9)) for i in [8, 17, 26]]])

        self._left_button = make_button(80, 'Track_Left')
        self._right_button = make_button(81, 'Track_Left')
        self._shift_button = make_button(82, 'Shift')

        self._leds = LedMatrixElement(rows=[make_leds(list(range(LED_START_CC_IDENTIFIER, LED_START_CC_IDENTIFIER + NUM_LEDS)), 'Leds_%d')])

    def _create_mixer(self):
        mixer = MixerComponent(controller=self, num_tracks=NUM_TRACKS, is_enabled=True, auto_name=True)
        mixer.layer = Layer(
            leds=self._leds,
            volume_controls=self._volume_faders,
            send_controls=self._send_encoders,
            master_fader=self._master_fader,
            master_encoders=self._master_encoders)

        mixer.on_send_index_changed = partial(self._show_controlled_sends_message, mixer)

        self.log_message("Mixer created")

        return mixer

    def _create_session(self):
        session = SessionComponent(num_tracks=NUM_TRACKS, is_enabled=True, auto_name=True, enable_skinning=True)
        session.layer = Layer(track_bank_left_button=self._left_button, track_bank_right_button=self._right_button)
        self._on_session_offset_changed.subject = session
        return session

    @subject_slot('offset')
    def _on_session_offset_changed(self):
        session = self._on_session_offset_changed.subject
        self._show_controlled_tracks_message(session)

    def _create_device(self):
        device = DeviceComponent(name='Device_Component', is_enabled=False, device_selection_follows_track_selection=True)
        device.layer = Layer(parameter_controls=self._pan_device_encoders, parameter_lights=self._pan_device_encoder_lights, priority=1)
        device_settings_layer = Layer(bank_buttons=self._state_buttons, prev_device_button=self._left_button, next_device_button=self._right_button, priority=1)
        mode = DeviceModeComponent(component=device, device_settings_mode=[
         AddLayerMode(device, device_settings_layer)], is_enabled=True)
        mode.layer = Layer(device_mode_button=self._pan_device_mode_button)
        return device

    def _show_controlled_sends_message(self, mixer):
        if mixer.send_index is not None:
            send_index = mixer.send_index
            send_name1 = chr(ord('A') + send_index)
            if send_index + 1 < mixer.num_sends:
                send_name2 = chr(ord('A') + send_index + 1)
                self.show_message('Controlling Send %s and %s' % (send_name1, send_name2))
            else:
                self.show_message('Controlling Send %s' % send_name1)
        return

    def _show_controlled_tracks_message(self, session):
        start = session.track_offset() + 1
        end = min(start + 8, len(session.tracks_to_use()))
        self.show_message('Controlling tracks %s to %s' % (start, end))

    def _send_live_template(self):
        self.log_message("Sending live template: %s" % (SYSEX_LIVE_TEMPLATE_SYSEX,))
        self._send_midi(SYSEX_LIVE_TEMPLATE_SYSEX)
        self._initialize_task.restart()

    def handle_sysex(self, midi_bytes):
        if midi_bytes[:6] == PREFIX_LIVE_TEMPLATE_SYSEX:
            if midi_bytes[6] == LIVE_CHANNEL:
                if self._initialize_task.is_running:
                    self._create_components()
                else:
                    self.update()
        else:
            super(KNTRL9, self).handle_sysex(midi_bytes)

    def send_midi(self, message, optimized=True):
        #self.log_debug_message("Call from %s" % str(inspect.stack()[1]))
        self._send_midi(message, optimized=optimized)

    def _send_midi(self, message, optimized = True):
        self.log_debug_message("send midi (optimized = %s): %s" % (str(optimized), str(message)))
        super(KNTRL9, self)._send_midi(message, optimized=optimized)

    def update(self):
        with self.component_guard():
            for control in self.controls:
                control.clear_send_cache()

            for component in self._components:
                component.update()

    def _do_log(self, *message):
        """ Writes the given message into Live's main log file """
        message = '(%s) %s' % (self.__class__.__name__, (' ').join(map(str, message)))
        if self._c_instance:
            self._c_instance.log_message(message)
        else:
            console_message = 'KNTRL9: ' + message
            logger.info(console_message)

    def log_error(self, *message):
        self._do_log("ERROR:")
        self._do_log(*message)

    def log_warning(self, *message):
        if LOG_LEVEL <= LOG_LEVEL_WARNING:
            self._do_log("WARNING:")
            self._do_log(*message)

    def log_message(self, *message):
        if LOG_LEVEL <= LOG_LEVEL_INFO:
            self._do_log(*message)

    def log_debug_message(self, *message):
        if LOG_LEVEL <= LOG_LEVEL_DEBUG:
            self._do_log(*message)

    def _send_identity_request(self):
        self._identity_response_pending = True
        self.log_message("Sending identity request...")
        self.log_message(self.identity_request)

        self._send_midi(self.identity_request)

    def disconnect(self):
        self._send_midi(SYSEX_GOODBYE_MESSAGE)
        super(KNTRL9, self).disconnect()
