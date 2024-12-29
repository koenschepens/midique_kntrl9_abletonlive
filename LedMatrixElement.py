# uncompyle6 version 3.4.1
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  2 2019, 14:32:10) 
# [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)]
# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Framework/LedMatrixElement.py
# Compiled at: 2019-04-09 19:23:45

from _Framework.CompoundElement import CompoundElement
from _Framework.Util import in_range, product, const, slicer, to_slice

class LedMatrixElement(CompoundElement):
    """
    Class representing a 2-dimensional set of leds.

    When using as a resource, leds might be individually grabbed at
    any time by other components. The matrix will automatically block
    messages coming from or sent to a led owned by them, and will
    return None when you try to query it.
    """

    def __init__(self, rows=[], *a, **k):
        super(LedMatrixElement, self).__init__(*a, **k)
        self._leds = []
        self._orig_leds = []
        self._led_coordinates = {}
        self._max_row_width = 0
        for row in rows:
            self.add_row(row)

    @property
    @slicer(2)
    def submatrix(self, col_slice, row_slice):
        col_slice = to_slice(col_slice)
        row_slice = to_slice(row_slice)
        rows = [ row[col_slice] for row in self._orig_leds[row_slice] ]
        return LedMatrixElement(rows=rows)

    def add_row(self, leds):
        self._leds.append([None] * len(leds))
        self._orig_leds.append(leds)
        for index, led in enumerate(leds):
            self._led_coordinates[led] = (
             index, len(self._leds) - 1)
            self.register_control_element(led)

        if self._max_row_width < len(leds):
            self._max_row_width = len(leds)
        return

    def width(self):
        return self._max_row_width

    def height(self):
        return len(self._leds)

    def send_color(self, column, row, r, g, b, force=False):
        assert in_range(r, 0, 255)
        assert in_range(g, 0, 255)
        assert in_range(b, 0, 255)
        assert in_range(column, 0, self.width())
        assert in_range(row, 0, self.height())
        if len(self._leds[row]) > column:
            led = self._leds[row][column]
            if led:
                led.send_value(r, g, b, force=force)

    def reset(self):
        for led in self:
            if led:
                led.reset()

    def __iter__(self):
        for j, i in product(list(range(self.height())), list(range(self.width()))):
            led = self.get_led(i, j)
            yield led

    def __getitem__(self, index):
        if isinstance(index, slice):
            indices = index.indices(len(self))
            return list(map(self._do_get_item, list(range(*indices))))
        else:
            if index < 0:
                index += len(self)
            return self._do_get_item(index)

    def _do_get_item(self, index):
        assert in_range(index, 0, len(self)), 'Index out of range'
        row, col = divmod(index, self.width())
        return self.get_led(col, row)

    def __len__(self):
        return self.width() * self.height()

    def iterleds(self):
        for j, i in product(list(range(self.height())), list(range(self.width()))):
            led = self.get_led(i, j)
            yield (led, (i, j))

    def on_nested_control_element_value(self, value, sender):
        x, y = self._led_coordinates[sender]
        assert self._leds[y][x]
        is_momentary = getattr(sender, 'is_momentary', const(None))()
        self.notify_value(value, x, y, is_momentary)
        return

    def on_nested_control_element_received(self, control):
        x, y = self._led_coordinates[control]
        self._leds[y][x] = control

    def on_nested_control_element_lost(self, control):
        x, y = self._led_coordinates[control]
        self._leds[y][x] = None
        return

    def get_led(self, column, row):
        assert in_range(column, 0, self.width())
        assert in_range(row, 0, self.height())
        if len(self._leds[row]) > column:
            return self._leds[row][column]
