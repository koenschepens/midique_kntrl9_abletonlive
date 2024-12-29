
try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

import traceback
from _Framework.Control import control_list, ButtonControl, Control
from _Framework.Util import nop
from _Framework.ChannelStripComponent import ChannelStripComponent as ChannelStripComponentBase
from _Framework.MixerComponent import MixerComponent as MixerComponentBase
from .LedElement import LedElement
from .LedControl import LedControl
from ableton.v2.base import listens, listens_group, EventObject, liveobj_valid
from functools import partial
from .Constants import *
from functools import partial
from _Framework import Task
import math

PARAMETER_PREFIX = "KNTRL9"
PARAMETER_PREFIX_LEN = len(PARAMETER_PREFIX)
NUM_ROWS = 2

def release_control(control):
    if control != None:
        control.release_parameter()
    return

def reset_button(button):
    if button != None:
        button.reset()
    return

class ChannelStripComponent(ChannelStripComponentBase):
    _led_control = LedControl()

    def __init__(self, controller, user_friendly_name):
        super(ChannelStripComponent, self).__init__()
        self.controller = controller
        self.user_friendly_name = user_friendly_name
        self.clipping = False
        self.needs_led_update = False
        # This is to indicate that the mixer currently is updating the tracks and no events should be fired.
        self._updating_tracks = False

        #self._blink_task_loop = self._tasks.add(Task.TaskGroup(loop=False, auto_kill=True))

        # This will update the blink color
        # TODO: This should be somewhere else IMO
        self._blink_task_loop = self._tasks.add(Task.loop(
            Task.wait(0.5),
            Task.run(partial(self._led_value, None, True)),
            Task.wait(0.5),
            Task.run(partial(self._led_value, CLIPPING_COLOR, True)),
        ))

        self._blink_task_loop.kill()

        # TODO : The Ableton Framework already provides functionality to keep track of the connected send controls
        # TODO : (slots?).
        # TODO : Replace _connected_send_controls with the corresponding Framework functionality
        self._connected_send_controls = {}
        self._led_control.log_message = self.log_debug_message

        '''def make_led_slot(name):
            return self.register_slot(None, getattr(self, '_%s_value' % name), 'value')

        self._led_slot = make_led_slot("led")'''

    def update(self):
        #self.log_debug_message("Updating channel %s" % self.user_friendly_name)
        super(ChannelStripComponent, self).update()

    def log_message(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_message(message)

    def log_debug_message(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_debug_message(message)

    def log_warning(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_warning(message)

    def log_error(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_error(message)

    def _connect_parameters(self):
        #self.log_debug_message("connect_parameters(): %d devices, connected controls: %d" % (len(self._track.devices), len(self._connected_send_controls)))

        # First do the default controls
        if self._pan_control is not None:
            self._pan_control.connect_to(self._track.mixer_device.panning)
        if self._volume_control is not None:
            self._volume_control.connect_to(self._track.mixer_device.volume)
        if self._send_controls is not None:
            index = 0
            # Connect the send controls to the sends until they are all connected. If not connected to a send,
            # connect the bottom control to the pan
            for send_control in self._send_controls:
                if send_control is not None and send_control not in list(self._connected_send_controls.values()):
                    if index < len(self._track.mixer_device.sends):
                        #self.log_debug_message("Connecting send_control %s to send index %d" % (send_control.name, index))
                        send_control.connect_to(self._track.mixer_device.sends[index])
                    elif index == 2:
                        # Connect to pan
                        send_control.connect_to(self._track.mixer_device.panning)
                    else:
                        send_control.release_parameter()
                        self._empty_control_slots.register_slot(send_control, nop, 'value')
                index += 1

        # Then optionally overwrite them with the KNTRL9 device controls
        for device in self._track.devices:
            for parameter in device.parameters:
                # For example: KNTRL9-1 will be send control 0
                send_control = self._get_parameter_send_control(parameter)
                if send_control is not None:
                    if send_control == self._volume_control:
                        self.log_debug_message("parameter type: %s" % type(parameter).__name__)
                        send_control.connect_to(parameter)
                    else:
                        send_control.connect_to(parameter)

        return

    def _disconnect_parameters(self):
        all_controls = self._all_controls()
        #self.log_debug_message("_disconnect_parameters(): %d controls" % len(all_controls))
        for control in all_controls:
            release_control(control)
            self._empty_control_slots.register_slot(control, nop, 'value')

        # Remove from the connected send control list
        # TODO This shouldn't be necessary! Use the Ableton Framework's own method to check for connected controls
        self._connected_send_controls.clear()
        #for parameter in self._connected_send_controls:
        #    del self._connected_send_controls[parameter]

    def _reconnect_parameters(self):
        self._disconnect_parameters()
        self._connect_parameters()

    @listens('selected_track')
    def __on_selected_track_changed(self):
        self.__on_selected_track_changed.subject = self.song().view.selected_track.view
        if self.device_selection_follows_track_selection:
            self.update_device_selection()

        self.log_debug_message("track selection CHANGED!!")

    @listens('value')
    def __on_volume_control_value_received(self, _):
        self.log_debug_message("VOL CHANGED!!")

    def _track_color_changed(self, send=True):
        if self.track:
            self.log_debug_message("Track %s COLOR CHANGED!!" % self._track.name)

            color_index = self.get_color_index(self._track.color)
            if color_index > 0:
                self.log_debug_message("Color %s was found in the index %d" % (self._track.color, color_index))

                self._led_value(color_index, send=send, force=True)
            else:
                self.log_warning("Color %s was not found in the index" % self._track.color)
        else:
            self._led_value(0, send=send, force=True)
            self.log_debug_message("self._track is None")

    def find_nearest_color(self, color):
        def color_compare(r1, g1, b1, r2, g2, b2):
            return math.sqrt(((r1 - r2) * (r1 - r2) + (g1 - g2) * (g1 - g2) + (b1 - b2) * (b1 - b2)))
            #return math.sqrt(((r1 - r2) * (r1 - r2)))

        def get_hue(color):
            r, g, b = getRGB(color)
            r, g, b = r / 255.0, g / 255.0, b / 255.0
            mx = max(r, g, b)
            mn = min(r, g, b)
            df = mx - mn
            if mx == mn:
                h = 0
            elif mx == r:
                h = (60 * ((g - b) / df) + 360) % 360
            elif mx == g:
                h = (60 * ((b - r) / df) + 120) % 360
            elif mx == b:
                h = (60 * ((r - g) / df) + 240) % 360
            if mx == 0:
                s = 0
            else:
                s = (df / mx) * 100
            v = mx * 100
            return h, s, v

        def getRGB(color):
            r = (color & 0xFF0000) >> 16
            g = (color & 0x00FF00) >> 8
            b = color & 0x0000FF

            return r, g, b

        tr, tg, tb = getRGB(color)
        th, ts, tv = get_hue(color)
        last_score = 255
        last_match = 0

        for match in LIVE_COLORS_TO_MIDI_VALUES:
            h, s, v = get_hue(match)
            score = color_compare(th, ts, tv, h, s, v)

            # print('%x > (%x %x %x) == (%x %x %x) scores %d' % (match, r,g,b, tr, tg, tb, score))
            if score == 0:
                return match

            if score < last_score:
                last_score = score
                last_match = match

        return last_match

    def get_color_index(self, color):

        if self.track:
            if color in LIVE_COLORS_TO_MIDI_VALUES:
                return LIVE_COLORS_TO_MIDI_VALUES[color]
            else:
                nearest_color = self.find_nearest_color(color)
                self.log_warning("Could not find color index of color %x. Defaulting to nearest (%x)" % (color, nearest_color))
                return LIVE_COLORS_TO_MIDI_VALUES[nearest_color]

        else:
            return 0

    def _devices_changed(self):
        self.log_debug_message("Device changed!")
        self.log_debug_message("Removing listeners")
        self._remove_listeners()
        self.log_debug_message("Reconnecting parameters")
        self._reconnect_parameters()
        self.log_debug_message("Done reconnecting parameters")

        self.log_debug_message("updating listeners")
        self._update_listeners()

    def set_track(self, track):
        def get_track_name(t):
            return t.name if t and t.name is not None else "None"

        self.log_debug_message("Replacing current track %s with new track %s" % (get_track_name(self._track), get_track_name(track)))
        self._remove_listeners()

        super(ChannelStripComponent, self).set_track(track)

        if self._led_control is not None:
            self._led_control.enabled = bool(track)

        self._update_listeners()
        # Update track color but don't send
        #self._track_color_changed(send=False)

    def set_led_control(self, control):
        if control != self._led_control:
            if self._led_control is not None:
                #self._led_control.release_parameter()
                #self._led_slot.subject = control
                self._led_control.set_control_element(control)

            #self._led_control = control
            self.update()

    def reset_led_on_exchange(self, led):
        if led is not None:
            led.reset()

    def get_led_rgb_index(self):
        if self._led_control is not None and self.track is not None:
            return self.get_color_index(self.track.color)
            #return self._led_control.get_rgb_index()
        else:
            return 0

    def _led_value(self, index, send=True, force=False):
        if self._led_control is None:
            raise AssertionError("Led is None!")

        if self.is_enabled():
            try:
                self._led_control.set_rgb_index(index)
                self.log_debug_message("_led_value: %s, send: %s, force: %s" % (index, send, force))

                if send or force:
                    self._led_control.update(force=force)
                else:
                    self.needs_led_update = True

            except Exception as e:
                self.log_error("Could not send color: %s" % e)

    def on_selected_track_changed(self):
        if self.is_enabled() and self._select_button is not None:
            if self._track is not None:
                color_index = self.get_color_index(self._track.color)
                if color_index >= 0:
                    self._led_control.set_rgb_index(color_index)
            else:
                self._led_control.set_rgb_index(0)
        return

    def _get_parameter_send_control(self, parameter):
        # Filter KNTRL9x parameters
        if str(parameter.name[:PARAMETER_PREFIX_LEN]).upper() == PARAMETER_PREFIX \
                and parameter.name[PARAMETER_PREFIX_LEN + 1:] in ["1", "2", "3", "4"]:

            self.log_debug_message("Found parameter with KNTRL9 prefix: %s" % parameter.name)

            # Get the corresponding index
            parameter_index = int(parameter.name[PARAMETER_PREFIX_LEN + 1:]) - 1

            if parameter_index == 3:
                self.log_debug_message("Slider")
                return self._volume_control

            if self._send_controls is not None and parameter_index < len(self._send_controls):
                self.log_debug_message("KNTRL9 detected. Index: (%d/%s)" % (parameter_index, len(self._send_controls)))
                return self._send_controls[parameter_index]

    def _update_parameter_name(self, parameter):
        self.log_debug_message("Updated name for parameter to %s" % parameter.name)
        self._connect_parameters()
        pass

        '''
        send_control = self._get_parameter_send_control(parameter)

        if send_control is not None:
            self.log_debug_message("Connecting %s to %s.%s" % (send_control.name, parameter.canonical_parent.name, parameter.name))
            send_control.connect_to(parameter)
            self._connected_send_controls[parameter] = send_control

        elif parameter in self._connected_send_controls:
            # The parameter was already connected to a send control. Since it now has changed, remove the old connection
            self.log_debug_message("Parameter was connected to send")

            # And connect to Send again.
            current_send_control = self._connected_send_controls[parameter]

            if current_send_control is not None:
                send_control_index = self._send_controls.index(current_send_control)
                #self.log_debug_message("This parameter (%s) was already connected to control with index %d" %(parameter.name, send_control_index))

                # Disconnect existing connection
                current_send_control.release_parameter()
                del self._connected_send_controls[parameter]

                # Reconnect to Send (if any)
                if send_control_index < len(self._track.mixer_device.sends):
                    current_send_control.connect_to(self._track.mixer_device.sends[send_control_index])
                elif send_control_index == 2:
                    # Connect to pan
                    current_send_control.connect_to(self._track.mixer_device.panning)
        else:
            # The parameter was not connected to any of the sends and also did not start with KNTRL9_. This only 
            # happens when a device with (a) KNTRL_ parameter(s) is pasted to a channel. Connect it to the send. This 
            # was not done before so we need to figure out which send control to connect it to
            for send_control in self._send_controls:
            for send_control in self._send_controls:
                if send_control is not None and parameter == parameter:
                    send_control.connect_to(parameter)
        '''

    def _sends_changed(self):
        self.log_debug_message("sends changed")
        pass

    def _track_info_changed(self):
        self.log_debug_message("info changed")
        self.log_debug_message("to: %s" % self._track.info)
        pass

    def _output_level_changed(self):
        if self._track == None:
            return

        if not self.clipping and self._track.output_meter_level > 0.90:
            self.clipping = True
            '''intensity = (self._track.output_meter_level - 0.9) * 10
            current_color_r = (self.track.color & 0xFF0000) >> 16
            current_color_g = (self.track.color & 0x00FF00) >> 8
            current_color_b = self.track.color & 0x0000FF

            clipping_color_r = int(current_color_r + ((0xFF - current_color_r) * intensity))
            clipping_color_g = int(current_color_g - (current_color_g * intensity))
            clipping_color_b = int(current_color_b - (current_color_b * intensity))
            self._led_value((clipping_color_r << 16) | (clipping_color_g << 8) | clipping_color_b)'''
            self._blink_task_loop.restart()

        elif self.clipping and self._track.output_meter_level <= 0.90:
            self.clipping = False
            self._blink_task_loop.pause()
            self._led_value(self.track.color)

    def _update_listeners(self):
        if self.track:
            self.log_debug_message("Updating listeners for track %s..." % self._track.name if self._track is not None else "None")

            self._track.add_color_listener(self._track_color_changed)
            self._track.add_devices_listener(self._devices_changed)
            self._track.add_output_meter_level_listener(self._output_level_changed)
            self._track.add_data_listener(self._track_info_changed)

            if any(self._track.mixer_device.sends):
                self._track.mixer_device.add_sends_listener(self._sends_changed)

            if any(self._track.devices):
                for device in self._track.devices:
                    for parameter in device.parameters:
                        self.log_debug_message("Adding name listener to parameter %s.%s.%s" % (self._track.name, device.name, parameter.name))
                        parameter.add_name_listener(partial(self._update_parameter_name, parameter))
                        # Run the name listener in case this device was copy-pasted with KNTRL9_x names
                        self._update_parameter_name(parameter)

    def _remove_listeners(self):
        if self._track:
            self.log_debug_message("self._track is now %s..." % self._track.name)
            track_name = str(self._track.name if self._track.name is not None else "<No name>")
            self.log_debug_message("Disable listeners for track %s..." % track_name)

            if self._track.color_has_listener(self._track_color_changed):
                #self.log_debug_message("Disable color listener %s..." % str(track_name))
                self._track.remove_color_listener(self._track_color_changed)

            if self._track.devices_has_listener(self._devices_changed):
                self._track.remove_devices_listener(self._devices_changed)

            if self._track.data_has_listener(self._track_info_changed):
                self._track.remove_data_listener(self._track_info_changed)

            if self._track.output_meter_level_has_listener(self._output_level_changed):
                self._track.remove_output_meter_level_listener(self._output_level_changed)

            if any(self._track.mixer_device.sends) and self._track.mixer_device.sends_has_listener(self._sends_changed):
                self._track.mixer_device.remove_sends_listener(self._sends_changed)

            if any(self._track.devices):
                for device in self._track.devices:
                    for parameter in device.parameters:
                        if parameter.name_has_listener(partial(self._update_parameter_name, parameter)):
                            #self.log_debug_message("Removing name listener from parameter %s.%s.%s" % (track_name, device.name, parameter.name))
                            parameter.remove_name_listener(partial(self._update_parameter_name, parameter))

class MasterChannelStripComponent(ChannelStripComponent):
    def _connect_parameters(self):
        self.log_debug_message("Master connect")
        for send_control, parameter in zip_longest(self._send_controls, self._get_all_parameters(3) or []):
            if send_control is not None and parameter is not None:
                send_control.connect_to(parameter)

        if self._volume_control is not None:
            self._volume_control.connect_to(self._track.mixer_device.volume)

    def _get_all_parameters(self, max):
        count = 0
        for device in self._track.devices:
            for parameter in device.parameters:
                self.log_debug_message('Parameter %s: quantized: %s, enabled: %s, min: %s, max: %s' % (parameter.name, parameter.is_quantized, parameter.is_enabled, parameter.min, parameter.max))
                if not parameter.is_quantized and parameter.is_enabled:
                    count += 1
                    if count <= max:
                        yield parameter
                    else:
                        break


class SelectedStripComponent(ChannelStripComponentBase):
    def __init__(self, controller, user_friendly_name):
        self.user_friendly_name = user_friendly_name
        self.controller = controller
        super(SelectedStripComponent, self).__init__()

    def log_message(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_message(message)

    def log_debug_message(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_debug_message(message)

    def log_warning(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_warning(message)

    def log_error(self, *message):
        message = 'Channel %s: %s' % (self.user_friendly_name, ' '.join(map(str, message)))
        self.controller.log_error(message)

    def disconnect(self):
        self.log_debug_message("disconnect")
        super(SelectedStripComponent, self).disconnect()

    def set_track(self, track):
        pass
        '''
        def get_track_name(t):
            return t.name if t is not None else "None"

        self.log_debug_message("Replacing current track %s with new track %s", (get_track_name(self._track), get_track_name(track)))

        super(SelectedStripComponent, self).set_track(track)
        '''

    def reset_button_on_exchange(self, button):
        super(SelectedStripComponent, self).reset_button_on_exchange(button)

    def _update_track_name_data_source(self):
        super(SelectedStripComponent, self)._update_track_name_data_source()

    def set_send_controls(self, controls):
        super(SelectedStripComponent, self).set_send_controls(controls)

    def set_pan_control(self, control):
        super(SelectedStripComponent, self).set_pan_control(control)

    def on_selected_track_changed(self):
        self.log_debug_message("on_selected_track_changed")
        super(SelectedStripComponent, self).on_selected_track_changed()

    def _connect_parameters(self):
        self.log_debug_message("_connect_parameters")
        super(SelectedStripComponent, self)._connect_parameters()

    def _disconnect_parameters(self):
        self.log_debug_message("_disconnect_parameters")
        for control in self._all_controls():
            self.log_debug_message("_disconnect_parameter %s" % control.name)
            release_control(control)
            self._empty_control_slots.register_slot(control, nop, 'value')

    def update(self):
        self.log_debug_message("_disconnect_parameters")
        super(SelectedStripComponent, self).update()

    def _select_value(self, value):
        self.log_debug_message("_select_value %s" % value)
        super(SelectedStripComponent, self)._select_value(value)
