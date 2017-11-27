
import threading
import time
import socket

from ..messages.data_packet import DataPacket
from ..receiver import LISTEN_ON_OPTIONS, E131_NETWORK_DATA_LOSS_TIMEOUT_ms

class receiverThread(threading.Thread):
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
            self.check_for_timeouts()
            # receive the data
            try:
                raw_data, ip_sender = list(self.sock.recvfrom(1024))
            except socket.timeout:
                continue  # if a timeout happens just go through while from the beginning
            try:
                tmp_packet = DataPacket.make_data_packet(raw_data)
            except:  # try to make a DataPacket. If it fails just go over it
                continue

            self.check_for_stream_terminated_and_refresh_timestamp(tmp_packet)
            self.check_and_refresh_priorities(tmp_packet)
            self.fire_callbacks_universe(tmp_packet)

    def check_for_timeouts(self):
        # check all DataTimestamps for timeouts
        for key, value in list(self.lastDataTimestamps.items()):
            if check_timeout(value):
                for callback in self.callbacks[LISTEN_ON_OPTIONS[0]]:
                    try:
                        callback(key)
                    except:
                        pass
                del self.lastDataTimestamps[key]

    def check_for_stream_terminated_and_refresh_timestamp(self, packet: DataPacket):
        # refresh the last timestamp on a universe, but check if its the last message of a stream
        # (the stream is terminated by the Stream termination bit)
        if packet.option_StreamTerminated:
            del self.lastDataTimestamps[packet.universe]  # delete the timestamp so that the callback is
            # not fired twice or more
            # fire callback
            for callback in self.callbacks[LISTEN_ON_OPTIONS[0]]:
                try:
                    callback(packet.universe)
                except:
                    pass
        else:
            self.lastDataTimestamps[packet.universe] = current_time_millis()

    def check_and_refresh_priorities(self, packet: DataPacket):
        # check the priority and refresh the priorities dict
        # first: check if the stored priority has timeouted and make the current packets priority the new one
        if packet.universe not in self.priorities.keys() or \
           self.priorities[packet.universe] is None or \
           check_timeout(self.priorities[packet.universe][1]) or \
           self.priorities[packet.universe][0] <= packet.priority:  # if the send priority is higher or
            # equal than the stored one, than make the priority the new one

            self.priorities[packet.universe] = (packet.priority, current_time_millis())

    def fire_callbacks_universe(self, packet: DataPacket):
        # call the listeners for the universe but before check if the data has changed
        # check if there are listeners for the universe before proceeding
        # check if the tmp_packet 's priority is high enough to get processed
        if packet.universe not in self.callbacks.keys() or \
           packet.priority < self.priorities[packet.universe][0]:
            return  # return if the universe is not interesting
        if packet.universe not in self.previousData.keys() or \
           self.previousData[packet.universe] is None or \
           self.previousData[packet.universe] != packet.dmxData:
            # set previous data and inherit callbacks
            self.previousData[packet.universe] = packet.dmxData
            for callback in self.callbacks[packet.universe]:
                callback(packet)


def current_time_millis():
    return int(round(time.time() * 1000))


def check_timeout(time):
    return abs(current_time_millis() - time) > E131_NETWORK_DATA_LOSS_TIMEOUT_ms
