# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This is a server for sending out sACN and receiving sACN data.
http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""

import random
from typing import Dict

from sacn.messages.data_packet import DataPacket
from sacn.sending.output import Output
from sacn.sending.output_thread import OutputThread, DEFAULT_PORT


class sACNsender:
    def __init__(self, bind_address: str = "0.0.0.0", bind_port: int = DEFAULT_PORT,
                 source_name: str = "default source name", cid: tuple = (),
                 fps: int = 30, universeDiscovery: bool = True):
        """
        Creates a sender object. A sender is used to manage multiple sACN universes and handles their sending.
        DMX data is send out every second, when no data changes. Some changes may be not send out, because the fps
        setting defines how often packets are send out to prevent network overuse. So if you change the DMX values too
        often in a second they may not all been send. Vary the fps parameter to your needs (Default=30).
        Note that a bind address is needed on Windows for sending out multicast packets.
        :param bind_address: the IP-Address to bind to.
        For multicast on a Windows machine this must be set to a proper value otherwise omit.
        :param bind_port: optionally bind to a specific port. Default=5568. It is not recommended to change the port.
        Change the port number if you have trouble with another program or the sACNreceiver blocking the port
        :param source_name: the source name used in the sACN packets.
        :param cid: the cid. If not given, a random CID will be generated.
        :param fps: the frames per second. See above explanation. Has to be >0
        """
        self.source_name: str = source_name
        if len(cid) != 16:
            cid = tuple(int(random.random() * 255) for _ in range(0, 16))
        self.__CID: tuple = cid
        self._outputs: Dict[int, Output] = {}
        self._fps = fps
        self.bindAddress = bind_address
        self.bind_port = bind_port
        self._output_thread: OutputThread = None
        self._universeDiscovery: bool = universeDiscovery

    @property
    def universeDiscovery(self) -> bool:
        return self._universeDiscovery
    @universeDiscovery.setter
    def universeDiscovery(self, universeDiscovery: bool) -> None:
        self._universeDiscovery = universeDiscovery
        try:  # try to set the value for the output thread
            self._output_thread.universeDiscovery = universeDiscovery
        except:
            pass

    @property
    def manual_flush(self) -> bool:
        return self._output_thread.manual_flush
    @manual_flush.setter
    def manual_flush(self, manual_flush: bool) -> None:
        self._output_thread.manual_flush = manual_flush

    def flush(self):
        self._output_thread.send_out_all_universes()

    def activate_output(self, universe: int) -> None:
        """
        Activates a universe that's then starting to sending every second.
        See http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf for more information
        :param universe: the universe to activate
        """
        check_universe(universe)
        # check, if the universe already exists in the list:
        if universe in self._outputs:
            return
        # add new sending:
        new_output = Output(DataPacket(cid=self.__CID, sourceName=self.source_name, universe=universe))
        self._outputs[universe] = new_output

    def deactivate_output(self, universe: int) -> None:
        """
        Deactivates an existing sending. Every data from the existing sending output will be lost.
        (TTL, Multicast, DMX data, ..)
        :param universe: the universe to deactivate. If the universe was not activated before, no error is raised
        """
        check_universe(universe)
        try:  # try to send out three messages with stream_termination bit set to 1
            self._outputs[universe]._packet.option_StreamTerminated = True
            for i in range(0, 3):
                self._output_thread.send_out(self._outputs[universe])
        except:
            pass
        try:
            del self._outputs[universe]
        except:
            pass

    def get_active_outputs(self) -> tuple:
        """
        Returns a list with all active outputs. Useful when iterating over all sender indexes.
        :return: list: a list with int (every int is a activated universe. May be not sorted)
        """
        return tuple(self._outputs.keys())

    def move_universe(self, universe_from: int, universe_to: int) -> None:
        """
        Moves an sending from one universe to another. All settings are being restored and only the universe changes
        :param universe_from: the universe that should be moved
        :param universe_to: the target universe. An existing universe will be overwritten
        """
        check_universe(universe_from)
        check_universe(universe_to)
        # store the sending object and change the universe in the packet of the sending
        tmp_output = self._outputs[universe_from]
        tmp_output._packet.universe = universe_to
        # deactivate sending
        self.deactivate_output(universe_from)
        # activate new sending with the new universe
        self._outputs[universe_to] = tmp_output

    def __getitem__(self, item: int) -> Output:
        try:
            return self._outputs[item]
        except:
            return None

    def start(self, bind_address=None, bind_port: int = None, fps: int = None) -> None:
        """
        Starts or restarts a new Thread with the parameters given in the constructor or
        the parameters given in this function.
        The parameters in this function do not override the class specific values!
        :param bind_address: the IP-Address to bind to
        :param bind_port: the port to bind to
        :param fps: the fps to use. Note: this is not precisely hold, use for load balance in the network
        """
        if bind_address is None:
            bind_address = self.bindAddress
        if fps is None:
            fps = self._fps
        if bind_port is None:
            bind_port = self.bind_port
        self.stop()
        self._output_thread = OutputThread(cid=self.__CID, source_name=self.source_name,
                                           outputs=self._outputs, bind_address=bind_address,
                                           bind_port=bind_port, fps=fps, universe_discovery=self._universeDiscovery)
        self._output_thread.start()

    def stop(self) -> None:
        """
        Tries to stop a current running sender. A running Thread will be stopped and should terminate.
        """
        try:
            self._output_thread.enabled_flag = False
        except:
            pass

    def __del__(self):
        # stop a potential running thread
        self.stop()


def check_universe(universe: int):
    if universe not in range(1, 64000):
        raise TypeError(f'Universe must be between [1-63999]! Universe was {universe}')
