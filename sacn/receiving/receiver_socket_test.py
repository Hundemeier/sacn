# This file is under MIT license. The license file can be obtained in the root directory of this module.


from sacn.receiving.receiver_socket_base import ReceiverSocketBase


class ReceiverSocketTest(ReceiverSocketBase):
    def __init__(self):
        super().__init__(listener=None)
        self.run_called: bool = False
        self.stop_called: bool = False
        self.join_multicast_called: str = None
        self.leave_multicast_called: str = None

    def run(self) -> None:
        self.run_called = True

    def stop(self) -> None:
        self.stop_called = True

    def join_multicast(self, multicast_addr: str) -> None:
        self.join_multicast_called = multicast_addr

    def leave_multicast(self, multicast_addr: str) -> None:
        self.leave_multicast_called = multicast_addr

    def call_on_data(self, data: bytes) -> None:
        self._listener.on_data(data)

    def call_on_periodic_callback(self) -> None:
        self._listener.on_periodic_callback()
