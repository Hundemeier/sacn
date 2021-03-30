# This file is under MIT license. The license file can be obtained in the root directory of this module.

import threading
import socket
import time
import logging

from sacn.sending.output import Output
from sacn.messages.universe_discovery import UniverseDiscoveryPacket
from sacn.messages.sync_packet import SyncPacket
from sacn.messages.data_packet import calculate_multicast_addr

DEFAULT_PORT = 5568
SEND_OUT_INTERVAL = 1
E131_E131_UNIVERSE_DISCOVERY_INTERVAL = 10
PER_ADDRESS_PRIORITY_INTERVAL = 1

# Timing compensation factor
INTERVAL_CORRECTION_FACTOR = 0.984
SEND_OUT_INTERVAL = SEND_OUT_INTERVAL * INTERVAL_CORRECTION_FACTOR
E131_E131_UNIVERSE_DISCOVERY_INTERVAL = E131_E131_UNIVERSE_DISCOVERY_INTERVAL * INTERVAL_CORRECTION_FACTOR
PER_ADDRESS_PRIORITY_INTERVAL = PER_ADDRESS_PRIORITY_INTERVAL * INTERVAL_CORRECTION_FACTOR


class OutputThread(threading.Thread):
    def __init__(self, cid: tuple, source_name: str, outputs: dict, bind_address,
                 bind_port: int = DEFAULT_PORT, fps: int = 30, universe_discovery: bool = True):
        super().__init__(name='sACN sending/sender thread')
        self.__CID: tuple = cid
        self._sourceName: str = source_name
        self._outputs: dict = outputs
        self._bindAddress = bind_address
        self.enabled_flag: bool = True
        self.fps: int = fps
        self._bind_port = bind_port
        self._socket: socket.socket = None
        self.universeDiscovery: bool = universe_discovery
        self.manual_flush: bool = False
        self.per_address_priority: bool = False
        self.logger = logging.getLogger('sacn')
        self._sync_sequence = 0

    def run(self):
        self.logger.info('Started sACN sender thread.')
        self._socket = socket.socket(socket.AF_INET,  # Internet
                                     socket.SOCK_DGRAM)  # UDP
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:  # noqa: E722 Not all systems support multiple sockets on the same port and interface
            pass

        try:
            self._socket.bind((self._bindAddress, self._bind_port))
            self.logger.info(f'Bind sender thread to IP:{self._bindAddress} Port:{self._bind_port}')
        except socket.error:
            self.logger.exception(f'Could not bind to IP:{self._bindAddress} Port:{self._bind_port}')
            raise

        last_time_uni_discover = 0
        self.enabled_flag = True
        while self.enabled_flag:
            time_stamp = time.time()

            # send out universe discovery packets if necessary
            if (abs(time.time() - last_time_uni_discover) > E131_E131_UNIVERSE_DISCOVERY_INTERVAL
               and self.universeDiscovery):    # TODO: swap bool first for short circuit execution
                self.send_uni_discover_packets()
                last_time_uni_discover = time.time()

            # iterate through outputs to send needed priorities
            # Note: dict may changes size during iteration (multithreading)
            [self.send_priority(output) for output in list(self._outputs.values())
             # send if changed or interval expired
             # Note: per address priority does not respect manual flush
             if (output.per_address_priority and
                 (output.per_address_priority_changed or
                  (abs(time.time() - output.last_priority_time) >= PER_ADDRESS_PRIORITY_INTERVAL)))]

            # go through the list of outputs and send everything out that has to be send out
            # Note: dict may changes size during iteration (multithreading)
            [self.send_out(output) for output in list(self._outputs.values())
             # only send if the manual flush feature is disabled
             # send out when the 1 second interval is over
             if not self.manual_flush and
             (abs(time.time() - output._last_time_send) > SEND_OUT_INTERVAL
              or output._changed)]   # TODO: swap bool first for short circuit execution

            time_to_sleep = (1 / self.fps) - (time.time() - time_stamp)
            if time_to_sleep < 0:  # if time_to_sleep is negative (because the loop has too much work to do) set it to 0
                time_to_sleep = 0
            time.sleep(time_to_sleep)
            # this sleeps nearly exactly so long that the loop is called every 1/fps seconds
        self._socket.close()
        self.logger.info('Stopped sACN sender thread')

    def send_out(self, output: Output):
        # 1st: Destination (check if multicast)
        if output.multicast:
            udp_ip = output._level_packet.calculate_multicast_addr()        # TODO: why calculate this on every send?
            # make socket multicast-aware: (set TTL)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, output.ttl)
        else:
            udp_ip = output.destination

        self.send_packet(output._level_packet, udp_ip)
        output._last_time_send = time.time()
        # increase the sequence counter
        output._level_packet.sequence_increase()
        # the changed flag is not necessary any more
        output._changed = False

    def send_priority(self, output: Output):
        # 1st: Destination (check if multicast)
        if output.multicast:
            udp_ip = output._level_packet.calculate_multicast_addr()        # TODO: why calculate this on every send?
            # make socket multicast-aware: (set TTL)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, output.ttl)
        else:
            udp_ip = output.destination

        # keep priority packets in sequence with level packets
        output._priority_packet.sequence = output._level_packet.sequence
        # increment level packet sequence for priority packet we sent
        output._level_packet.sequence_increase()
        # send priority packet
        self.send_packet(output._priority_packet, udp_ip)
        # store the last time we output priority
        output.last_priority_time = time.time()
        # clear changed flag
        output.per_address_priority_changed = False

    def send_uni_discover_packets(self):  # hint: on windows a bind address must be set, to use broadcast
        packets = UniverseDiscoveryPacket.make_multiple_uni_disc_packets(
            cid=self.__CID, sourceName=self._sourceName, universes=list(self._outputs.keys()))
        for packet in packets:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.send_packet(packet=packet, destination='<broadcast>')

    def send_packet(self, packet, destination: str):
        MESSAGE = bytearray(packet.getBytes())
        try:
            self._socket.sendto(MESSAGE, (destination, DEFAULT_PORT))
        except OSError as e:
            self.logger.warning('Failed to send packet', exc_info=e)

    def send_out_all_universes(self, sync_universe: int, universes: dict):
        """
        Sends out all universes in one go. This is not done by this thread! This is done by the caller's thread.
        This uses the E1.31 sync mechanism to try to sync all universes.
        Note that not all receivers support this feature.
        Also 0xDD per address priority packets are not within the manual flush framework
        """
        # go through the list of outputs and send everything out
        # Note: dict may changes size during iteration (multithreading)
        for output in list(universes.values()):
            output._level_packet.syncAddr = sync_universe  # temporarily set the sync universe
            self.send_out(output)
            output._level_packet.syncAddr = 0
        sync_packet = SyncPacket(cid=self.__CID, syncAddr=sync_universe, sequence=self._sync_sequence)
        # Increment sequence number for next time.
        self._sync_sequence += 1
        if self._sync_sequence > 255:
            self._sync_sequence = 0
        self.send_packet(sync_packet, calculate_multicast_addr(sync_universe))
