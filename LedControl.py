
from functools import partial
from _Framework import Task
from _Framework.Defaults import MOMENTARY_DELAY
from _Framework.SubjectSlot import SlotManager
from _Framework.Util import clamp, lazy_attribute, mixin, nop, first, second, is_matrix, flatten, product
from _Framework.Control import control_event, ButtonControl
from .Constants import *

class LedControl(ButtonControl):
    value = control_event('value')

    class State(SlotManager):
        enabled = True

        def __init__(self, control=None, manager=None, channel=None, identifier=None, *a, **k):
            super(LedControl.State, self).__init__(*a, **k)
            # To determine if the LED value needs to be sent
            self._dirty = True
            assert control is not None
            assert manager is not None

            self._rgb_index = 0
            self._manager = manager
            self._value_listener = control._event_listeners.get('value', None)
            self._event_listeners = control._event_listeners
            self._control = control
            self._control_element = None
            self._value_slot = None
            self.enable_updates = True
            self._channel = channel
            self._identifier = identifier
            self._register_value_slot(manager, control)

            self._msg_identifier = channel
            self._msg_channel = identifier

            manager.register_slot_manager(self)

        def set_log_message(self, log_message):
            self.log_message = log_message

        def set_control_element(self, control_element):
            self._control_element = control_element
            if self._control_element:
                self._control_element.reset_state()
                if self._channel is not None:
                    self._control_element.set_channel(self._channel)
                if self._identifier is not None:
                    self._control_element.set_identifier(self._identifier)
            if self._value_slot:
                self._value_slot.subject = control_element
            return

        def _register_value_slot(self, manager, control):
            if self._event_listener_required():
                self._value_slot = self.register_slot(None, self._on_value, 'value')
            return

        def _event_listener_required(self):
            return len(self._event_listeners) > 0

        def _on_value(self, value, *a, **k):
            if self._value_listener and self._notifications_enabled():
                self._value_listener(self._manager, value, self, *a, **k)

        def _notifications_enabled(self):
            return self.enabled and self._manager.control_notifications_enabled()

        def _get_channel(self):
            return self._channel

        def _set_channel(self, channel):
            self._channel = channel
            if self._control_element:
                self._control_element.set_channel(self._channel)

        channel = property(_get_channel, _set_channel)

        def _get_identifier(self):
            return self._identifier

        def _set_identifier(self, value):
            self._identifier = value
            if self._control_element:
                self._control_element.set_identifier(self._identifier)

        def set_rgb_index(self, value):
            self._dirty = True
            self._rgb_index = value

        def get_rgb_index(self):
            return self._rgb_index

        def update(self, force=False):
            self._dirty = False
            if self._control_element is not None and self.enable_updates:
                self._control_element.send_value(self._rgb_index, force=force)

        def reset(self):
            self._dirty = True
            self.set_rgb_index(0)

        def message_channel(self):
            return self._msg_channel

        def message_identifier(self):
            return self._msg_identifier

        identifier = property(_get_identifier, _set_identifier)

    _extra_kws = {}
    _extra_args = []

    def __init__(self, extra_args=None, extra_kws=None, *a, **k):
        super(LedControl, self).__init__(*a, **k)
        self._event_listeners = {}
        if extra_args is not None:
            self._extra_args = extra_args
        if extra_kws is not None:
            self._extra_kws = extra_kws
        return

