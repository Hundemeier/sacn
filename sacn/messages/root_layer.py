'''
This represents a root layer of an ACN Message.
Information about sACN: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
'''

_FIRST_INDEX = \
    (0, 0x10, 0, 0, 0x41, 0x53, 0x43, 0x2d, 0x45,
     0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00)


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
