# This file is under MIT license. The license file can be obtained in the root directory of this module.

from sacn.messages.data_packet import DataPacket


class Output:
    # TODO Porting the packet: 

    """
    This class is a compact representation of an sending with all relevant information
    """
    def __init__(self, packet: DataPacket, last_time_send = 0, destination = "127.0.0.1",
                 multicast = False, ttl = 8):
        self._packet: DataPacket = packet       # TODO Port packet:
        self._last_time_send = last_time_send
        self.destination = destination
        self.multicast = multicast
        self.ttl = ttl
        self._changed = False

    @property
    def dmx_data(self):
        return self._packet.dmxData
    @dmx_data.setter
    def dmx_data(self, dmx_data):
        self._packet.dmxData = dmx_data
        self._changed = True

    @property
    def priority(self):
        return self._packet.priority
    @priority.setter
    def priority(self, priority):
        self._packet.priority = priority

    @property
    def preview_data(self):
        return self._packet.option_PreviewData
    @preview_data.setter
    def preview_data(self, preview_data):
        self._packet.option_PreviewData = preview_data

#
# class customList(list):
#     def __init__(self, args):
#         super().__init__(args)
#         self.callbacks: list = []
#
#     def __setitem__(self, key, value):
#         super().__setitem__(key, value)
#         for callback in self.callbacks:
#             callback()
