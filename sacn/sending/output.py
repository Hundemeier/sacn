# This file is under MIT license. The license file can be obtained in the root directory of this module.

from sacn.messages.data_packet import DataPacket
from copy import deepcopy


class Output:
    """
    This class is a compact representation of a universe's status with all relevant information
    """
    def __init__(self, packet: DataPacket, last_time_send: int = 0, destination: str = "127.0.0.1",
                 multicast: bool = False, ttl: int = 8):
        self._level_packet: DataPacket = packet
        self._last_time_send: int = last_time_send
        self.destination: str = destination
        self.multicast: bool = multicast
        self.ttl: int = ttl
        self._changed: bool = False
        self._priority_packet: DataPacket = deepcopy(self._level_packet)
        self._priority_packet.dmxStartCode = 0xDD
        self._last_priority_time: float = 0
        self._per_address_priority: bool = False
        self._per_address_priority_changed: bool = False

    @property
    def dmx_data(self) -> tuple:
        return self._level_packet.dmxData

    @dmx_data.setter
    def dmx_data(self, dmx_data: tuple):
        self._level_packet.dmxData = dmx_data
        self._changed = True

    @property
    def per_address_priority_data(self) -> tuple:
        return self._priority_packet.dmxData

    @per_address_priority_data.setter
    def per_address_priority_data(self, priority_data: tuple):
        self._priority_packet.dmxData = priority_data
        # applying data implies turning on priority
        self._per_address_priority = True
        self._per_address_priority_changed = True

    @property
    def per_address_priority_changed(self) -> bool:
        return self._per_address_priority_changed

    @per_address_priority_changed.setter
    def per_address_priority_changed(self, per_address_priority_changed):
        self._per_address_priority_changed = per_address_priority_changed

    @property
    def per_address_priority(self) -> bool:
        return self._per_address_priority

    @per_address_priority.setter
    def per_address_priority(self, per_address_priority: bool):
        self._per_address_priority = per_address_priority
        if self._per_address_priority:
            # default to full universe at packet priority
            self._priority_packet.dmxData = ((self._level_packet.priority,) * 512)
        self._per_address_priority_changed = True

    @property
    def priority(self) -> int:
        return self._level_packet.priority

    @priority.setter
    def priority(self, priority: int):
        # if using per_address_priority and current priority packet content matches full universe at old priority (default)
        if self._per_address_priority and (self._level_packet_priority == sum(self._priority_packet.dmxData) / 512):
            # default to full universe at new packet priority
            self._priority_packet.dmxData = ((priority,) * 512)
        self._level_packet.priority = priority
        self._priority_packet.priority = priority

    @property
    def preview_data(self) -> bool:
        return self._level_packet.option_PreviewData

    @preview_data.setter
    def preview_data(self, preview_data: bool):
        self._level_packet.option_PreviewData = preview_data
        self._priority_packet.option_PreviewData = preview_data

