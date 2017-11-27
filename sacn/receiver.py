# This file is under MIT license. The license file can be obtained in the root directory of this module.

import socket
import threading
import time

from .messages.data_packet import DataPacket, calculate_multicast_addr

E131_NETWORK_DATA_LOSS_TIMEOUT_ms = 2500
LISTEN_ON_OPTIONS = ("timeout", "test")

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
        self._callbacks = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:  # Not all systems support multiple sockets on the same port and interface
            pass
        self.sock.bind((bind_address, bind_port))

    def listen_universe(self, universe: int):
        """
        This is a decorator for callbacks that should react on the given universe.
        The callbacks are getting inherited if the dmx data was changed
        :param universe: the universe to listen on
        """
        def decorator(f: callable):
            self.register_universe_callback(universe=universe, func=f)
            return f
        return decorator

    def register_universe_callback(self, universe: int, func: callable):
        """
        Register a callback for the given universe and type. You can also use the decorator function 'listen_universe'
        for the same result. The callbacks are only called, when the DMX data on the universe has changed.
        :param universe: the universe on which the callback should be registered
        :param func: the callback
        """
        # add callback to the _callbacks list for the universe
        try:
            self._callbacks[universe].append(func)
        except:  # try to append
            self._callbacks[universe] = [func]

    def listen_on(self, trigger: str):
        """
        This is a simple decorator for registering a callback for an event. You can also use 'register_listener'
        :param trigger: Currently supported options: 'timeout'
        """
        def decorator(f):
            self.register_listener(trigger=trigger, func=f)
            return f
        return decorator

    def register_listener(self, trigger: str, func: callable):
        """
        Register a listener for the given trigger. Raises an TypeError when the trigger is not a valid one.
        To get a list with all valid triggers, use 'from receiver import LISTEN_ON_OPTIONS'.
        :param trigger: the trigger on which the given callback should be used
        :param func: the callback. The parameters depend on the trigger. See README for more information
        """
        if trigger in LISTEN_ON_OPTIONS:
            try:
                self._callbacks[trigger].append(func)
            except:
                self._callbacks[trigger] = [func]
        else:
            raise TypeError(f'The given trigger "{trigger}" is not a valid one!')


    def join_multicast(self, universe: int):
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

    def leave_multicast(self, universe: int):
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

    def start(self):
        """
        Starts a new thread that handles the input. If a thread is already running, the thread will be restarted.
        """
        self.stop()  # stop an existing thread
        self._thread = _receiverThread(sock=self.sock, callbacks=self._callbacks)
        self._thread.start()

    def stop(self):
        """
        Stops a running thread. If no thread was started nothing happens.
        """
        try:
            self._thread.enabled_flag = False
        except:  # try to stop the thread
            pass

    def get_possible_universes(self):
        """
        Get all universes that are possible because a data packet was received. Timeouted data is removed from the list,
        so the list may change over time. Depending on sources that are shutting down their streams.
        :return: a tuple with all universes that were received so far and hadn't a timeout
        """
        return tuple(self._thread.lastDataTimestamps.keys())

    def __del__(self):
        # stop a potential running thread
        self.stop()


class _receiverThread(threading.Thread):
    def __init__(self, sock: socket.socket, callbacks: dict):
        """
        This is a private class and should not be used elsewhere. It handles the while loop running in the thread.
        :param socket: the socket to use to listen. It will not be initalized and only the socket.recv function is used.
        And the socket.settimeout function is also used
        :param callbacks: the list with all callbacks
        """
        self.enabled_flag = True
        self.sock = sock
        self.callbacks = callbacks
        # previousData for storing the last data that was send in a universe to check if the data has changed
        self.previousData = {}
        # priorities are stored here. This is for checking if the incoming data has the best priority.
        self.priorities = {}
        # store the last timestamp when something on an universe arrived for checking for timeouts
        self.lastDataTimestamps = {}
        super().__init__(name='sACN input/receiver thread')

    def run(self):
        self.sock.settimeout(0.1)  # timeout as 100ms
        self.enabled_flag = True
        while self.enabled_flag:
            # before receiving: check for timeouts
            for key, value in self.lastDataTimestamps.items():
                if check_timeout(value):
                    for callback in self.callbacks[LISTEN_ON_OPTIONS[0]]:
                        try:
                            callback(key)
                        except:
                            pass
                        del self.lastDataTimestamps[key]
                        continue  # ToDo: make the loop safe for deleting items from the dict

            try:
                raw_data, ip_sender = list(self.sock.recvfrom(1024))
            except socket.timeout:
                continue  # if a timeout happens just go through while from the beginning
            try:
                tmp_packet = DataPacket.make_data_packet(raw_data)
            except:  # try to make a DataPacket. If it fails just go over it
                continue

            # refresh the last timestamp on a universe, but check if its the last message of a stream
            # (the stream is terminated by the Stream termination bit)
            if tmp_packet.option_StreamTerminated:
                self.lastDataTimestamps.pop(tmp_packet.universe, None)
                # fire callback
                for callback in self.callbacks[LISTEN_ON_OPTIONS[0]]:
                    try:
                        callback(tmp_packet.universe)
                    except:
                        pass
            else:
                self.lastDataTimestamps[tmp_packet.universe] = current_time_millis()

            # check the priority and refresh the priorities dict
            # first: check if the stored priority has timeouted and make the current packets priority the new one
            if tmp_packet.universe not in self.priorities.keys() or \
               self.priorities[tmp_packet.universe] is None or \
               check_timeout(self.priorities[tmp_packet.universe][1]) or \
               self.priorities[tmp_packet.universe][0] <= tmp_packet.priority:  # if the send priority is higher or
                # equal than the stored one, than make the priority the new one
                self.priorities[tmp_packet.universe] = (tmp_packet.priority, current_time_millis())

            # call the listeners for the universe but before check if the data has changed
            # check if there are listeners for the universe before proceeding
            # check if the tmp_packet 's priority is high enough to get processed
            if tmp_packet.universe not in self.callbacks.keys() or \
               tmp_packet.priority < self.priorities[tmp_packet.universe][0]:
                continue
            if tmp_packet.universe not in self.previousData.keys() or \
               self.previousData[tmp_packet.universe] is None or \
               self.previousData[tmp_packet.universe] != tmp_packet.dmxData:
                # set previous data and inherit callbacks
                self.previousData[tmp_packet.universe] = tmp_packet.dmxData
                for callback in self.callbacks[tmp_packet.universe]:
                    callback(tmp_packet)


def current_time_millis():
    return int(round(time.time() * 1000))

def check_timeout(time):
    return abs(current_time_millis() - time) > E131_NETWORK_DATA_LOSS_TIMEOUT_ms
