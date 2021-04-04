# This file is under MIT license. The license file can be obtained in the root directory of this module.


from sacn.sending.sender_socket_base import SenderSocketBase


class SenderSocketTest(SenderSocketBase):
    def __init__(self, listener=None):
        super().__init__(listener)
        self.start_called: bool = False
        self.stop_called: bool = False
        self.send_unicast_called: (bytearray, str) = None
        self.send_multicast_called: (bytearray, str, int) = None
        self.send_broadcast_called: (bytearray) = None

    def start(self) -> None:
        self.start_called = True

    def stop(self) -> None:
        self.stop_called = True

    def send_unicast(self, data: bytearray, destination: str) -> None:
        self.send_unicast_called = (data, destination)

    def send_multicast(self, data: bytearray, destination: str, ttl: int) -> None:
        self.send_multicast_called = (data, destination, ttl)

    def send_broadcast(self, data: bytearray) -> None:
        self.send_broadcast_called = (data)

    def call_on_periodic_callback(self) -> None:
        self._listener.on_periodic_callback()
