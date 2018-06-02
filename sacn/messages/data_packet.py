# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This represents a framing layer and a DMP layer from the E1.31 Standard
Information about sACN: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""
from sacn.messages.root_layer import VECTOR_DMP_SET_PROPERTY, \
    VECTOR_E131_DATA_PACKET, \
    VECTOR_ROOT_E131_DATA, \
    RootLayer, \
    int_to_bytes, \
    make_flagsandlength


class DataPacket(RootLayer):
    def __init__(self, cid: tuple, sourceName: str, universe: int, dmxData: tuple = (), priority: int = 100,
                 sequence: int = 0, streamTerminated: bool = False, previewData: bool = False,
                 forceSync: bool = False, sync_universe: int = 0):
        self._vector1 = VECTOR_E131_DATA_PACKET
        self._vector2 = VECTOR_DMP_SET_PROPERTY
        self.sourceName: str = sourceName
        self.priority = priority
        self.syncAddr = sync_universe
        self.universe = universe
        self.option_StreamTerminated: bool = streamTerminated
        self.option_PreviewData: bool = previewData
        self.option_ForceSync: bool = forceSync
        self.sequence = sequence
        self.dmxData = dmxData
        super().__init__(126 + len(dmxData), cid, VECTOR_ROOT_E131_DATA)

    def __str__(self):
        return f'sACN DataPacket: Universe: {self.universe}, Priority: {self.priority}, Sequence: {self.sequence} ' \
               f'CID: {self._cid}'

    @property
    def priority(self) -> int:
        return self._priority
    @priority.setter
    def priority(self, priority: int):
        if priority not in range(0, 201):
            raise TypeError(f'priority must be in range [0-200]! value was {priority}')
        self._priority = priority

    @property
    def universe(self) -> int:
        return self._universe
    @universe.setter
    def universe(self, universe: int):
        if universe not in range(1, 64000):
            raise TypeError(f'universe must be [1-63999]! value was {universe}')
        self._universe = universe

    @property
    def syncAddr(self) -> int:
        return self._syncAddr
    @syncAddr.setter
    def syncAddr(self, sync_universe: int):
        if sync_universe not in range(0, 64000):
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

    @property
    def dmxData(self) -> tuple:
        return self._dmxData
    @dmxData.setter
    def dmxData(self, data: tuple):
        """
        For legacy devices and to prevent errors, the length of the DMX data is normalized to 512
        """
        newData = [0]*512
        for i in range(0, min(len(data), 512)):
            newData[i] = data[i]
        self._dmxData = tuple(newData)
        # in theory this class supports dynamic length, so the next line is correcting the length
        self.length = 126 + len(self._dmxData)

    def getBytes(self) -> tuple:
        rtrnList = super().getBytes()
        # Flags and Length Framing Layer:-------
        rtrnList.extend(make_flagsandlength(self.length - 38))
        # Vector Framing Layer:-----------------
        rtrnList.extend(self._vector1)
        # sourceName:---------------------------
        # make a 64 byte long sourceName
        tmpSourceName = [0] * 64
        for i in range(0, min(len(tmpSourceName), len(self.sourceName))):
            tmpSourceName[i] = ord(self.sourceName[i])
        rtrnList.extend(tmpSourceName)
        # priority------------------------------
        rtrnList.append(self._priority)
        # syncAddress---------------------------
        rtrnList.extend(int_to_bytes(self._syncAddr))
        # sequence------------------------------
        rtrnList.append(self._sequence)
        # Options Flags:------------------------
        tmpOptionsFlags = 0
        # stream terminated:
        tmpOptionsFlags += int(self.option_StreamTerminated) << 6
        # preview data:
        tmpOptionsFlags += int(self.option_PreviewData) << 7
        # force synchronization
        tmpOptionsFlags += int(self.option_ForceSync) << 5
        rtrnList.append(tmpOptionsFlags)
        # universe:-----------------------------
        rtrnList.extend(int_to_bytes(self._universe))
        # DMP Layer:---------------------------------------------------
        # Flags and Length DMP Layer:-----------
        rtrnList.extend(make_flagsandlength(self.length - 115))
        # Vector DMP Layer:---------------------
        rtrnList.append(self._vector2)
        # Some static values (Address & Data Type, First Property addr, ...)
        rtrnList.extend([0xa1, 0x00, 0x00, 0x00, 0x01])
        # Length of the data:-------------------
        lengthDmxData = len(self._dmxData)+1
        rtrnList.extend(int_to_bytes(lengthDmxData))
        # DMX data:-----------------------------
        rtrnList.append(0x00)  # DMX Start Code
        rtrnList.extend(self._dmxData)

        return tuple(rtrnList)

    @staticmethod
    def make_data_packet(raw_data) -> 'DataPacket':
        """
        Converts raw byte data to a sACN DataPacket. Note that the raw bytes have to come from a 2016 sACN Message.
        This does not support DMX Start code!
        :param raw_data: raw bytes as tuple or list
        :return: a DataPacket with the properties set like the raw bytes
        """
        # Check if the length is sufficient
        if len(raw_data) < 126:
            raise TypeError('The length of the provided data is not long enough! Min length is 126!')
        # Check if the three Vectors are correct
        if tuple(raw_data[18:22]) != tuple(VECTOR_ROOT_E131_DATA) or \
           tuple(raw_data[40:44]) != tuple(VECTOR_E131_DATA_PACKET) or \
           raw_data[117] != VECTOR_DMP_SET_PROPERTY:  # REMEMBER: when slicing: [inclusive:exclusive]
            raise TypeError('Some of the vectors in the given raw data are not compatible to the E131 Standard!')

        tmpPacket = DataPacket(cid=raw_data[22:38], sourceName=str(raw_data[44:108]),
                               universe=(0xFF * raw_data[113]) + raw_data[114])  # high byte first
        tmpPacket.priority = raw_data[108]
        tmpPacket.syncAddr = (0xFF * raw_data[109]) + raw_data[110]  # high byte first
        tmpPacket.sequence = raw_data[111]
        tmpPacket.option_PreviewData = bool(raw_data[112] & 0b10000000)  # use the 7th bit as preview_data
        tmpPacket.option_StreamTerminated = bool(raw_data[112] & 0b01000000)  # use bit 6 as stream terminated
        tmpPacket.option_ForceSync = bool(raw_data[112] & 0b00100000)  # use bit 5 as force sync
        tmpPacket.dmxData = raw_data[126:638]
        return tmpPacket

    def calculate_multicast_addr(self) -> str:
        return calculate_multicast_addr(self.universe)


def calculate_multicast_addr(universe: int) -> str:
    hi_byte = universe >> 8  # a little bit shifting here
    lo_byte = universe & 0xFF  # a little bit mask there
    return f"239.255.{hi_byte}.{lo_byte}"
