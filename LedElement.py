
import Live
import logging
from _Framework.Control import control_list, ButtonControl
from _Framework.DeviceComponent import DeviceComponent as DeviceComponentBase
from _Framework.ModesComponent import EnablingModesComponent, tomode
from _Framework.SysexValueControl import SysexValueControl
from _Framework.InputControlElement import InputControlElement, MIDI_CC_TYPE, MIDI_CC_STATUS
from _Framework.ButtonElement import ButtonElement
from .Constants import *

logger = logging.getLogger(__name__)

'''
This element represents an LED
'''
class LedElement(ButtonElement):
    _default_value = (0x00, 0x00, 0x00)

    def __init__(self, surface, index, midi_channel=0, *a, **k):
        '''
        Initialize an LED element
        :param midi_controller: the controller number (the address of the LED)
        :param midi_channel: the midi channel
        :param a:
        :param k:
        '''
        self._midi_channel = midi_channel
        self._msg_identifier = index
        self._msg_channel = midi_channel
        self.surface = surface
        self._index = index
        self._value = 0x0
        # We don't want the element to send out separate MIDI CC for each led. This will be done at once using SYSEX.
        self._send_immediately = False
        super(LedElement, self).__init__(is_momentary=True, channel=midi_channel, identifier=index, msg_type=MIDI_CC_TYPE, *a, **k)

    '''
    Sends the color of the current LED element to the controller
    '''
    def send_value(self, value, force=False):
        if self._send_immediately or force:
            message = (MIDI_CC_STATUS | self._midi_channel, self._index, value)
            if self._value != value:
                self.surface.send_midi(message, optimized = False)
                self._value = value
        else:
            if self._value != value:
                self._value = value

    def message_channel(self):
        return self._msg_channel

    def message_identifier(self):
        return self._msg_identifier