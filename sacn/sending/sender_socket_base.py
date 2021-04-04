# This file is under MIT license. The license file can be obtained in the root directory of this module.

import logging


class SenderSocketListener:
    """
    Base class for listener of a SenderSocketListener.
    """

    def on_periodic_callback(self) -> None:
        raise NotImplementedError


class SenderSocketBase:
    """
    Base class for abstracting a UDP sending socket.
    """

    def __init__(self, listener: SenderSocketListener):
        self._logger: logging.Logger = logging.getLogger('sacn')
        self._listener: SenderSocketListener = listener

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def send_unicast(self, data: bytearray, destination: str) -> None:
        raise NotImplementedError

    def send_multicast(self, data: bytearray, destination: str, ttl: int) -> None:
        raise NotImplementedError

    def send_broadcast(self, data: bytearray) -> None:
        raise NotImplementedError
