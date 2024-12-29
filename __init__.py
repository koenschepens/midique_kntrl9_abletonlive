# uncompyle6 version 3.4.1
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  2 2019, 14:32:10) 
# [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)]
# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/Launch_Control_XL/__init__.py
# Compiled at: 2019-04-09 19:23:44

from .KNTRL9 import KNTRL9
from _Framework.Capabilities import controller_id, inport, outport, CONTROLLER_ID_KEY, PORTS_KEY, NOTES_CC, SCRIPT, AUTO_LOAD_KEY

def get_capabilities():
    return {CONTROLLER_ID_KEY: controller_id(vendor_id=0x04D8, product_ids=[0xEBD4], model_name='Midique KNTRL9'),
       PORTS_KEY: [
                 inport(props=[NOTES_CC, SCRIPT]),
                 outport(props=[NOTES_CC, SCRIPT])], 
       AUTO_LOAD_KEY: True}


def create_instance(c_instance):
    return KNTRL9(c_instance)