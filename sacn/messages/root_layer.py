# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This represents a root layer of an ACN Message.
Information about sACN: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""

_FIRST_INDEX = \
    (0, 0x10, 0, 0, 0x41, 0x53, 0x43, 0x2d, 0x45,
     0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00)

VECTOR_E131_DATA_PACKET = (0, 0, 0, 0x02)
VECTOR_DMP_SET_PROPERTY = 0x02
VECTOR_ROOT_E131_DATA = (0, 0, 0, 0x4)

VECTOR_ROOT_E131_EXTENDED = (0, 0, 0, 0x8)

VECTOR_E131_EXTENDED_SYNCHRONIZATION = (0, 0, 0, 0x1)
VECTOR_E131_EXTENDED_DISCOVERY = (0, 0, 0, 0x2)
VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST = (0, 0, 0, 0x1)


class RootLayer:
    def __init__(self, length: int, cid: tuple, vector: tuple):
        self.length = length
        if(len(vector) != 4):
            raise ValueError('the length of the vector is not 4!')
        self._vector = vector
        if(len(cid) != 16):
            raise ValueError('the length of the CID is not 16!')
        self._cid = cid

    def getBytes(self) -> list:
        '''Returns the Root layer as list with bytes'''
        tmpList = []
        tmpList.extend(_FIRST_INDEX)
        # first append the high byte from the Flags and Length
        # high 4 bit: 0x7 then the bits 8-11(indexes) from _length
        length = self.length - 16
        tmpList.append((0x7 << 4) + (length >> 8))
        # Then append the lower 8 bits from _length
        tmpList.append(length & 0xFF)

        tmpList.extend(self._vector)
        tmpList.extend(self._cid)
        return tmpList

    @property
    def length(self) -> int:
        return self._length
    @length.setter
    def length(self, value: int):
        self._length = value & 0xFFF  # only use the least 12-Bit


def int_to_bytes(integer: int) -> list:
    """
    Converts a single integer number to an list with the length 2 with highest byte first.
    The returned list contains values in the range [0-255]
    :param integer: the integer to convert
    :return: the list with the high byte first
    """
    return [(integer >> 8) & 0xFF, integer & 0xFF]


def make_flagsandlength(length: int) -> list:
    """
    Converts a length value in a Flags and Length list with two bytes in the correct order.
    :param length: the length to convert. should be 12-bit value
    :return: the list with the two bytes
    """
    return [(0x7 << 4) + ((length & 0xF00) >> 8), length & 0xFF]
