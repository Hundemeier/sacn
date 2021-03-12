# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This implements the sync packet from the E1.31 standard.
Information about sACN: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""
from sacn.messages.root_layer import \
    VECTOR_ROOT_E131_EXTENDED, \
    VECTOR_E131_EXTENDED_SYNCHRONIZATION, \
    RootLayer, \
    byte_tuple_to_int, \
    int_to_bytes, \
    make_flagsandlength


class SyncPacket(RootLayer):
    def __init__(self, cid: tuple, syncAddr: int, sequence: int = 0):
        self._cid = cid
        self._syncAddr = syncAddr
        self._sequence = sequence
        super().__init__(49, cid, VECTOR_ROOT_E131_EXTENDED)

    @RootLayer.cid.setter
    def cid(self, cid: tuple):
        if (len(cid) != 16 or not all(isinstance(x, int) for x in cid) or not all(0 <= x <= 255 for x in cid)):
            raise TypeError(f'cid must be a 16 byte tuple! value was {cid}')
        super().__init__(49, cid, VECTOR_ROOT_E131_EXTENDED)
        self._cid = cid

    @property
    def syncAddr(self) -> int:
        return self._syncAddr

    @syncAddr.setter
    def syncAddr(self, sync_universe: int):
        if sync_universe not in range(1, 64000):
            raise TypeError(f'sync_universe must be [1-63999]! value was {sync_universe}')
        self._syncAddr = sync_universe

    @property
    def sequence(self) -> int:
        return self._sequence

    @sequence.setter
    def sequence(self, sequence: int):
        if sequence not in range(0, 256):
            raise TypeError(f'Sequence is a byte! values: [0-255]! value was {sequence}')
        self._sequence = sequence

    def sequence_increase(self):
        self._sequence += 1
        if self._sequence > 0xFF:
            self._sequence = 0

    def getBytes(self) -> tuple:
        rtrnList = super().getBytes()
        rtrnList.extend(make_flagsandlength(self.length - 38))
        rtrnList.extend(VECTOR_E131_EXTENDED_SYNCHRONIZATION)
        rtrnList.append(self._sequence)
        rtrnList.extend(int_to_bytes(self._syncAddr))
        rtrnList.extend((0, 0))  # the empty reserved slots
        return rtrnList

    @staticmethod
    def make_sync_packet(raw_data) -> 'SyncPacket':
        """
        Converts raw byte data to a sACN SyncPacket. Note that the raw bytes have to come from a 2016 sACN Message.
        :param raw_data: raw bytes as tuple or list
        :return: a SyncPacket with the properties set like the raw bytes
        """
        # Check if the length is sufficient
        if len(raw_data) < 47:
            raise TypeError('The length of the provided data is not long enough! Min length is 47!')
        # Check if the three Vectors are correct
        if tuple(raw_data[18:22]) != tuple(VECTOR_ROOT_E131_EXTENDED) or \
           tuple(raw_data[40:44]) != tuple(VECTOR_E131_EXTENDED_SYNCHRONIZATION):
            # REMEMBER: when slicing: [inclusive:exclusive]
            raise TypeError('Some of the vectors in the given raw data are not compatible to the E131 Standard!')
        tmpPacket = SyncPacket(cid=raw_data[22:38], syncAddr=byte_tuple_to_int(raw_data[45:47]))
        tmpPacket.sequence = raw_data[44]
        return tmpPacket
