# This file is under MIT license. The license file can be obtained in the root directory of this module.

import socket
from typing import Tuple

E131_NETWORK_DATA_LOSS_TIMEOUT_ms = 2500
LISTEN_ON_OPTIONS = ("availability", "universe")
# this has to be up here, because otherwise we have a circular import that can not import those two

from sacn.receiving.receiver_thread import receiverThread
from sacn.messages.data_packet import calculate_multicast_addr


class sACNreceiver:
    def __init__(self, bind_address: str = '0.0.0.0', bind_port: int = 5568):
        """
        Make a receiver for sACN data. Do not forget to start and add callbacks for receiving messages!
        :param bind_address: if you are on a Windows system and want to use multicast provide a valid interface
        IP-Address! Otherwise omit.
        :param bind_port: Default: 5568. It is not recommended to change this value!
        Only use when you are know what you are doing!
        """
        # If you bind to a specific interface on the Mac, no multicast data will arrive.
        # If you try to bind to all interfaces on Windows, no multicast data will arrive.
        self._bindAddress = bind_address
        self._thread = None
        self._callbacks = {'availability': [],
                           'universe': []} # init with empty list, because otherwise an error gets thrown
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:  # Not all systems support multiple sockets on the same port and interface
            pass
        self.sock.bind((bind_address, bind_port))

    def listen_on(self, trigger: str, **kwargs) -> callable:
        """
        This is a simple decorator for registering a callback for an event. You can also use 'register_listener'.
        A list with all possible options is available via LISTEN_ON_OPTIONS.
        :param trigger: Currently supported options: 'universe availability change', 'universe'
        """
        def decorator(f):
            self.register_listener(trigger, f, **kwargs)
            return f
        return decorator

    def register_listener(self, trigger: str, func: callable, **kwargs) -> None:
        """
        Register a listener for the given trigger. Raises an TypeError when the trigger is not a valid one.
        To get a list with all valid triggers, use LISTEN_ON_OPTIONS.
        :param trigger: the trigger on which the given callback should be used. 
        Currently supported: 'universe availability change', 'universe'
        :param func: the callback. The parameters depend on the trigger. See README for more information
        """
        if trigger in LISTEN_ON_OPTIONS:
            if trigger == LISTEN_ON_OPTIONS[1]:  # if the trigger is universe, use the universe from args as key
                try:
                    self._callbacks[kwargs[LISTEN_ON_OPTIONS[1]]].append(func)
                except:
                    self._callbacks[kwargs[LISTEN_ON_OPTIONS[1]]] = [func]
            try:
                self._callbacks[trigger].append(func)
            except:
                self._callbacks[trigger] = [func]
        else:
            raise TypeError(f'The given trigger "{trigger}" is not a valid one!')

    def join_multicast(self, universe: int) -> None:
        """
        Joins the multicast address that is used for the given universe. Note: If you are on Windows you must have given
        a bind IP-Address for this feature to function properly. On the other hand you are not allowed to set a bind
        address if you are on any other OS.
        :param universe: the universe to join the multicast group.
        The network hardware has to support the multicast feature!
        """
        self.sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
                             socket.inet_aton(calculate_multicast_addr(universe)) +
                             socket.inet_aton(self._bindAddress))

    def leave_multicast(self, universe: int) -> None:
        """
        Try to leave the multicast group with the specified universe. This does not throw any exception if the group
        could not be leaved.
        :param universe: the universe to leave the multicast group.
        The network hardware has to support the multicast feature!
        """
        try:
            self.sock.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP,
                                 socket.inet_aton(calculate_multicast_addr(universe)) +
                                 socket.inet_aton(self._bindAddress))
        except:  # try to leave the multicast group for the universe
            pass

    def start(self) -> None:
        """
        Starts a new thread that handles the input. If a thread is already running, the thread will be restarted.
        """
        self.stop()  # stop an existing thread
        self._thread = receiverThread(socket=self.sock, callbacks=self._callbacks)
        self._thread.start()

    def stop(self) -> None:
        """
        Stops a running thread. If no thread was started nothing happens.
        """
        try:
            self._thread.enabled_flag = False
        except:  # try to stop the thread
            pass

    def get_possible_universes(self) -> Tuple[int]:
        """
        Get all universes that are possible because a data packet was received. Timeouted data is removed from the list,
        so the list may change over time. Depending on sources that are shutting down their streams.
        :return: a tuple with all universes that were received so far and hadn't a timeout
        """
        return tuple(self._thread.lastDataTimestamps.keys())

    def __del__(self):
        # stop a potential running thread
        self.stop()
