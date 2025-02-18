# This file is under MIT license. The license file can be obtained in the root directory of this module.

from copy import deepcopy
from sacn.messages.data_packet import DataPacket


class Output:
    """
    This class is a compact representation of an sending with all relevant information
    """

    def __init__(self, packet: DataPacket, last_time_send: int = 0, destination: str = '127.0.0.1',
                 multicast: bool = False, ttl: int = 8):
        self._packet: DataPacket = packet
        self._last_time_send: int = last_time_send
        self.destination: str = destination
        self.multicast: bool = multicast
        self.ttl: int = ttl
        self._per_address_priority: tuple = ()
        self._changed: bool = False

    @property
    def dmx_data(self) -> tuple:
        return self._packet.dmxData

    @dmx_data.setter
    def dmx_data(self, dmx_data: tuple):
        self._packet.dmxData = dmx_data
        self._changed = True

    @property
    def priority(self) -> int:
        return self._packet.priority

    @priority.setter
    def priority(self, priority: int):
        self._packet.priority = priority

    @property
    def per_address_priority(self) -> tuple:
        return self._per_address_priority

    @per_address_priority.setter
    def per_address_priority(self, per_address_priority: tuple):
        if len(per_address_priority) != 512 and len(per_address_priority) != 0 or \
                not all((isinstance(x, int) and (0 <= x <= 255)) for x in per_address_priority):
            raise ValueError(f'per_address_priority is a tuple with a length of 512 or 0! '
                             f'Data in the tuple has to be valid bytes (i.e. values in range [0; 255])! '
                             f'Length was {len(per_address_priority)}')
        self._per_address_priority = per_address_priority

    @property
    def _per_address_priority_packet(self) -> DataPacket:
        per_address_priority_packet = deepcopy(self._packet)
        per_address_priority_packet.dmxStartCode = 0xdd
        per_address_priority_packet.dmxData = self.per_address_priority
        return per_address_priority_packet

    @property
    def preview_data(self) -> bool:
        return self._packet.option_PreviewData

    @preview_data.setter
    def preview_data(self, preview_data: bool):
        self._packet.option_PreviewData = preview_data
