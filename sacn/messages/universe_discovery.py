"""
This class represents an universe discovery packet of the E1.31 Standard.
"""
from typing import List

from sacn.messages.root_layer import RootLayer, VECTOR_ROOT_E131_EXTENDED, \
    VECTOR_E131_EXTENDED_DISCOVERY, VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST,\
    make_flagsandlength, int_to_bytes


class UniverseDiscoveryPacket(RootLayer):
    def __init__(self, cid: tuple, sourceName: str, universes: tuple, page: int = 0, lastPage: int = 0):
        self.sourceName: str = sourceName
        self._page: int = page
        self._lastPage: int = lastPage
        self._universes: list = universes
        super().__init__((len(universes)*2)+120, cid, VECTOR_ROOT_E131_EXTENDED)

    @property
    def page(self) -> int:
        return self._page
    @page.setter
    def page(self, page: int):
        if page not in range(0, 256):
            raise TypeError(f'Page is a byte! values: [0-255]! value was {page}')
        self._page = page

    @property
    def lastPage(self) -> int:
        return self._page
    @lastPage.setter
    def lastPage(self, lastPage: int):
        if lastPage not in range(0, 256):
            raise TypeError(f'Page is a byte! values: [0-255]! value was {lastPage}')
        self._page = lastPage

    @property
    def universes(self) -> tuple:
        return tuple(self._universes)
    @universes.setter
    def universes(self, universes: tuple):
        if len(universes) > 512:
            raise TypeError(f'Universes is a tuple with a max length of 512! The data in the tuple has to be int! '
                            f'Length was {len(universes)}')
        self._universes = sorted(universes)
        self.length = 121+(len(universes)*2)  # generate new length value for the packet

    def getBytes(self) -> tuple:
        rtrnList = super().getBytes()
        # Flags and Length Framing Layer:--------------------
        rtrnList.extend(make_flagsandlength(self.length - 38))
        # Vector Framing Layer:------------------------------
        rtrnList.extend(VECTOR_E131_EXTENDED_DISCOVERY)
        # source Name Framing Layer:-------------------------
        # make a 64 byte long sourceName
        tmpSourceName = [0] * 64
        for i in range(0, min(len(tmpSourceName), len(self.sourceName))):
            tmpSourceName[i] = ord(self.sourceName[i])
        rtrnList.extend(tmpSourceName)
        # reserved fields:-----------------------------------
        rtrnList.extend([0]*4)
        # Universe Discovery Layer:-------------------------------------
        # Flags and Length:----------------------------------
        rtrnList.extend(make_flagsandlength(self.length - 112))
        # Vector UDL:----------------------------------------
        rtrnList.extend(VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST)
        # page:----------------------------------------------
        rtrnList.append(self._page & 0xFF)
        # last page:-----------------------------------------
        rtrnList.append(self._lastPage & 0xFF)
        # universes:-----------------------------------------
        for universe in self._universes:  # universe is a 16-bit number!
            rtrnList.extend(int_to_bytes(universe))

        return tuple(rtrnList)

    @staticmethod
    def make_universe_discovery_packet(raw_data) -> 'UniverseDiscoveryPacket':
        # Check if the length is sufficient
        if len(raw_data) < 120:
            raise TypeError('The length of the provided data is not long enough! Min length is 120!')
        # Check if the three Vectors are correct
        # REMEMBER: when slicing: [inclusive:exclusive]
        if tuple(raw_data[18:22]) != tuple(VECTOR_ROOT_E131_EXTENDED) or \
           tuple(raw_data[40:44]) != tuple(VECTOR_E131_EXTENDED_DISCOVERY) or \
           tuple(raw_data[114:118]) != tuple(VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST):
            raise TypeError('Some of the vectors in the given raw data are not compatible to the E131 Standard!')

        # tricky part: convert plain bytes to a useful list of 16-bit values for further use
        # Problem: the given raw_byte can be longer than the dynamic length of the list of universes
        # first: extract the length from the Universe Discovery Layer (UDL)
        length = (two_bytes_to_int(raw_data[112], raw_data[113]) & 0xFFF) - 8
        # remember: UDL has 8 bytes plus the universes
        # remember: Flags and length includes a 12-bit length field
        universes = convert_raw_data_to_universes(raw_data[120:120+length])
        tmp_packet = UniverseDiscoveryPacket(cid=raw_data[22:38], sourceName=str(raw_data[44:108]), universes=universes)
        tmp_packet._page = raw_data[118]
        tmp_packet._lastPage = raw_data[119]
        return tmp_packet

    @staticmethod
    def make_multiple_uni_disc_packets(cid: tuple, sourceName: str, universes: list) -> List['UniverseDiscoveryPacket']:
        """
        Creates a list with universe discovery packets based on the given data. It creates automatically enough packets
        for the given universes list.
        :param cid: the cid to use in all packets
        :param sourceName: the source name to use in all packets
        :param universes: the universes. Can be longer than 512, but has to be shorter than 256*512.
        The values in the list should be [1-63999]
        :return: a list full of universe discovery packets
        """
        tmpList = []
        if len(universes)%512 != 0:
            num_of_packets = int(len(universes)/512)+1
        else:  # just get how long the list has to be. Just read and think about the if statement.
            # Should be self-explaining
            num_of_packets = int(len(universes)/512)
        universes.sort()  # E1.31 wants that the send out universes are sorted
        for i in range(0, num_of_packets):
            if i == num_of_packets-1:
                tmpUniverses = universes[i * 512:len(universes)]
                # if we are here, then the for is in the last loop
            else:
                tmpUniverses = universes[i * 512:(i+1) * 512]
            # create new UniverseDiscoveryPacket and append it to the list. Page and lastPage are getting special values
            tmpList.append(UniverseDiscoveryPacket(cid=cid, sourceName=sourceName, universes=tmpUniverses,
                                                   page=i, lastPage=num_of_packets-1))
        return tmpList


def convert_raw_data_to_universes(raw_data) -> tuple:
    """
    converts the raw data to a readable universes tuple. The raw_data is scanned from index 0 and has to have
    16-bit numbers with high byte first. The data is converted from the start to the beginning!
    :param raw_data: the raw data to convert
    :return: tuple full with 16-bit numbers
    """
    if len(raw_data)%2 != 0:
        raise TypeError('The given data has not a length that is a multiple of 2!')
    rtrnList = []
    for i in range(0, len(raw_data), 2):
        rtrnList.append(two_bytes_to_int(raw_data[i], raw_data[i+1]))
    return tuple(rtrnList)


def two_bytes_to_int(hi_byte: int, low_byte: int) -> int:
    """
    Converts two bytes to a normal integer value.
    :param hi_byte: the high byte
    :param low_byte: the low byte
    :return: converted integer that has a value between [0-65535]
    """
    return ((hi_byte & 0xFF)*256) + (low_byte & 0xFF)
