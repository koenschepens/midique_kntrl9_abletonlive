NUM_TRACKS = 8
NUM_LEDS = 9
LED_START_CC_IDENTIFIER = 0x70

LIVE_CHANNEL = 7

SYSEX_IDENTITY_REQUEST = [
	0xF0, #< Start Sysex
	0x7E, #< Non real-time
	0x00, #< Sysex Channel
	0x06, #< General Information
	0x02, #< Identity request
	0xF7  #< Start Sysex
]

SYSEX_MANUFACTURER_ID = (0x00, 0x50, 0x01)
SYSEX_PRODUCT_ID = SYSEX_MANUFACTURER_ID + (0x01,)

PREFIX_LIVE_TEMPLATE_SYSEX = (0xF0,) + SYSEX_PRODUCT_ID + (0x66,)
SYSEX_LIVE_TEMPLATE_SYSEX = PREFIX_LIVE_TEMPLATE_SYSEX + (LIVE_CHANNEL, 0xF7)

SYSEX_IDENTITY_RESPONSE = (0xF0, 126, 0, 6, 1) + SYSEX_PRODUCT_ID + (0xF7,)
SYSEX_GOODBYE_MESSAGE = (0xF0,) + SYSEX_PRODUCT_ID + (ord('G'), ord('O'), ord('O'), ord('D'), ord('B'), ord('Y'), ord('E'), 0xF7)
SYSEX_DUMP = (0xF0,) + SYSEX_PRODUCT_ID + (0x71, 0xF7)
SYSEX_SET_COLORS_RED_START = (0xF0,) + SYSEX_PRODUCT_ID + (0x21,)
SYSEX_END = (0xF7,)

SYSEX_COMMAND_SET_ALL_COLORS = 0x21

LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 20
LOG_LEVEL_WARNING = 40
LOG_LEVEL_ERROR = 60

LOG_LEVEL = LOG_LEVEL_WARNING

DEBUG = False

RED_MASK = 0xFF0000
GREEN_MASK = 0x00FF00
BLUE_MASK = 0x0000FF

CLIPPING_COLOR = 0xFF0000

'''
The colors will be divided by this number to make them less bright. This should eventually be done on the device.
Warning: This value should never exceed 2 because it is also taking care of the max MIDI message size!
'''
LED_FRACTION = 4

TOP_ENCODERS = [l * 3 for l in range(0, 9)]
BOTTOM_ENCODERS = [(l * 3) + 1 for l in range(0, 9)]

# Maps the RGB colors used in Live to an index used by the MIDI controller
LIVE_COLORS_TO_MIDI_VALUES = {
    0: 0,
    13013643: 1,
    16725558: 2,
    15597486: 3,
    14837594: 4,
    12026454: 5,
    16249980: 6,
    13872497: 7,
    10056267: 8,
    8912743: 9,
    8237133: 10,
    8754719: 11,
    2490280: 12,
    13958625: 13,
    6094824: 14,
    2319236: 15,
    32192: 16,
    11442405: 17,
    3101346: 18,
    1716118: 19,
    12558270: 20,
    11958214: 21,
    15029152: 22,
    13381230: 23,
    12349846: 24,
    5480241: 25,
    695438: 26,
    8623052: 27,
    6441901: 28,
    8092539: 29,
    3947580: 30,
    12565097: 31,
    10927616: 32,
    4047616: 33,
    49071: 34,
    1090798: 35,
    5538020: 36,
    8940772: 37,
    10701741: 38,
    16149507: 39,
    12581632: 40,
    1769263: 41,
    10208397: 42,
    1698303: 43,
    9611263: 44,
    10851765: 45,
    14183652: 46,
    16726484: 47,
    16753961: 48,
    16773172: 49,
    14402304: 50,
    13408551: 51,
    8962746: 52,
    8758722: 53,
    10204100: 54,
    10060650: 55,
    16749734: 56,
    16753524: 57,
    13821080: 58,
    12243060: 59,
    11119017: 60,
    13496824: 61,
    12173795: 62,
    13482980: 63,
    13684944: 64,
    15064289: 65,
    11481907: 66,
    7491393: 67,
    11096369: 68,
    16777215: 69,
    9160191: 70
}

RGB_COLORS = [
    0,
    1973790,
    8355711,
    16777215,
    16731212,
    16711680,
    5832704,
    1638400,
    16760172,
    16733184,
    5840128,
    2562816,
    16777036,
    16776960,
    5855488,
    1644800,
    8978252,
    5570304,
    1923328,
    1321728,
    5046092,
    65280,
    22784,
    6400,
    5046110,
    65305,
    22797,
    6402,
    5046152,
    65365,
    22813,
    7954,
    5046199,
    65433,
    22837,
    6418,
    5030911,
    43519,
    16722,
    4121,
    5015807,
    22015,
    7513,
    2073,
    5000447,
    255,
    89,
    25,
    8867071,
    5505279,
    1638500,
    983088,
    16731391,
    16711935,
    5832793,
    1638425,
    16731271,
    16711764,
    5832733,
    2228243,
    16717056,
    10040576,
    7950592,
    4416512,
    211200,
    22325,
    21631,
    255,
    17743,
    2425036,
    8355711,
    2105376,
    16711680,
    12451629,
    11529478,
    6618889,
    1084160,
    65415,
    43519,
    11007,
    4129023,
    7995647,
    11672189,
    4202752,
    16730624,
    8970502,
    7536405,
    65280,
    3931942,
    5898097,
    3735500,
    5999359,
    3232198,
    8880105,
    13835775,
    16711773,
    16744192,
    12169216,
    9502464,
    8609031,
    3746560,
    1330192,
    872504,
    1381674,
    1450074,
    6896668,
    11010058,
    14569789,
    14182940,
    16769318,
    10412335,
    6796559,
    1973808,
    14483307,
    8454077,
    10131967,
    9332479,
    4210752,
    7697781,
    14745599,
    10485760,
    3473408,
    1757184,
    475648,
    12169216,
    4141312,
    11755264,
    4920578]