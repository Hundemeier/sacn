
import threading
import time
import socket
import logging
from typing import Dict

from sacn.messages.data_packet import DataPacket
from sacn.receiver import LISTEN_ON_OPTIONS, E131_NETWORK_DATA_LOSS_TIMEOUT_ms


class receiverThread(threading.Thread):
    def __init__(self, socket, callbacks: Dict[any, list]):
        """
        This is a private class and should not be used elsewhere. It handles the while loop running in the thread.
        :param socket: the socket to use to listen. It will not be initalized and only the socket.recv function is used.
        And the socket.settimeout function is also used
        :param callbacks: the list with all callbacks
        """
        self.enabled_flag = True
        self.socket = socket
        self.callbacks: dict = callbacks
        # previousData for storing the last data that was send in a universe to check if the data has changed
        self.previousData: dict = {}
        # priorities are stored here. This is for checking if the incoming data has the best priority.
        # universes are the keys and
        # the value is a tuple with the last priority and the time when this priority recently was received
        self.priorities: Dict[int, tuple] = {}
        # store the last timestamp when something on an universe arrived for checking for timeouts
        self.lastDataTimestamps: dict = {}
        # store the last sequence number of a universe here:
        self.lastSequence: dict = {}
        self.logger = logging.getLogger('sacn')
        super().__init__(name='sACN input/receiver thread')

    def run(self):
        self.logger.info(f'Started new sACN receiver thread')
        self.socket.settimeout(0.1)  # timeout as 100ms
        self.enabled_flag = True
        while self.enabled_flag:
            # before receiving: check for timeouts
            self.check_for_timeouts()
            # receive the data
            try:
                raw_data, ip_sender = list(self.socket.recvfrom(1144))  # 1144 because the longest possible packet
                # in the sACN standard is the universe discovery packet with a max length of 1144
            except socket.timeout:
                continue  # if a timeout happens just go through while from the beginning
            try:
                tmp_packet = DataPacket.make_data_packet(raw_data)
            except:  # try to make a DataPacket. If it fails just go over it
                continue
            self.logger.debug(f'Received sACN packet:\n{tmp_packet}')

            self.check_for_stream_terminated_and_refresh_timestamp(tmp_packet)
            self.refresh_priorities(tmp_packet)
            if not self.is_legal_priority(tmp_packet):
                continue
            if not self.is_legal_sequence(tmp_packet):  # check for bad sequence number
                continue
            self.fire_callbacks_universe(tmp_packet)
        self.logger.info('Stopped sACN receiver thread')

    def check_for_timeouts(self) -> None:
        # check all DataTimestamps for timeouts
        for key, value in list(self.lastDataTimestamps.items()):
            #  this is converted to list, because the length of the dict changes
            if check_timeout(value):
                self.fire_timeout_callback_and_delete(key)

    def check_for_stream_terminated_and_refresh_timestamp(self, packet: DataPacket) -> None:
        # refresh the last timestamp on a universe, but check if its the last message of a stream
        # (the stream is terminated by the Stream termination bit)
        if packet.option_StreamTerminated:
            self.fire_timeout_callback_and_delete(packet.universe)
        else:
            # check if we add or refresh the data in lastDataTimestamps
            if packet.universe not in self.lastDataTimestamps.keys():
                for callback in self.callbacks[LISTEN_ON_OPTIONS[0]]:
                    try:  # fire callbacks if this is the first received packet for this universe
                        callback(universe=packet.universe, changed='available')
                    except:
                        pass
            self.lastDataTimestamps[packet.universe] = current_time_millis()

    def fire_timeout_callback_and_delete(self, universe: int):
        for callback in self.callbacks[LISTEN_ON_OPTIONS[0]]:
            try:
                callback(universe=universe, changed='timeout')
            except:
                pass
        # delete the timestamp so that the callback is not fired multiple times
        del self.lastDataTimestamps[universe]
        # delete sequence entries so that no packet out of order problems occur
        try:
            del self.lastSequence[universe]
        except Exception:
            pass # sometimes an error occurs here TODO: check why here comes an error

    def refresh_priorities(self, packet: DataPacket) -> None:
        # check the priority and refresh the priorities dict
        # check if the stored priority has timeouted and make the current packets priority the new one
        if packet.universe not in self.priorities.keys() or \
           self.priorities[packet.universe] is None or \
           check_timeout(self.priorities[packet.universe][1]) or \
           self.priorities[packet.universe][0] <= packet.priority:  # if the send priority is higher or
            # equal than the stored one, than make the priority the new one
            self.priorities[packet.universe] = (packet.priority, current_time_millis())

    def is_legal_sequence(self, packet: DataPacket) -> bool:
        """
        Check if the Sequence number of the DataPacket is legal.
        For more information see page 17 of http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf.
        :param packet: the packet to check
        :return: true if the sequence is legal. False if the sequence number is bad
        """
        # if the sequence of the packet is smaller than the last received sequence, return false
        # therefore calculate the difference between the two values:
        try:  # try, because self.lastSequence might not been initialized
            diff = packet.sequence - self.lastSequence[packet.universe]
            # if diff is between ]-20,0], return False for a bad packet sequence
            if 0 >= diff > -20:
                return False
        except:
            pass
        # if the sequence is good, return True and refresh the list with the new value
        self.lastSequence[packet.universe] = packet.sequence
        return True

    def is_legal_priority(self, packet: DataPacket):
        """
        Check if the given packet has high enough priority for the stored values for the packet's universe.
        :param packet: the packet to check
        :return: returns True if the priority is good. Otherwise False
        """
        # check if the packet's priority is high enough to get processed
        if packet.universe not in self.callbacks.keys() or \
           packet.priority < self.priorities[packet.universe][0]:
            return False  # return if the universe is not interesting
        else:
            return True

    def fire_callbacks_universe(self, packet: DataPacket) -> None:
        # call the listeners for the universe but before check if the data has changed
        # check if there are listeners for the universe before proceeding
        if packet.universe not in self.previousData.keys() or \
           self.previousData[packet.universe] is None or \
           self.previousData[packet.universe] != packet.dmxData:
            self.logger.debug('')
            # set previous data and inherit callbacks
            self.previousData[packet.universe] = packet.dmxData
            for callback in self.callbacks[packet.universe]:
                callback(packet)


def current_time_millis():
    return int(round(time.time() * 1000))


def check_timeout(time):
    return abs(current_time_millis() - time) > E131_NETWORK_DATA_LOSS_TIMEOUT_ms
