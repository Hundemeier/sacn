"""
This is a server for sending out sACN and receiving sACN data.
http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""

import random

from .messages.data_packet import DataPacket
from .output.output import Output
from .output.output_thread import OutputThread, DEFAULT_PORT


class sACNsender:
    def __init__(self, bind_address: str = "0.0.0.0", bind_port: int = DEFAULT_PORT, source_name: str = "default source name",
                 cid: tuple = (), fps: int = 30):
        """
        Creates a sender object. A sender is used to manage multiple sACN universes and handles their output.
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
        self._outputs = {}
        self._fps = fps
        self.bindAddress = bind_address
        self.bind_port = bind_port
        self._output_thread: OutputThread = None

    def activate_output(self, universe: int):
        """
        Activates a universe that's then starting to output every second.
        See http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf for more information
        :param universe: the universe to activate
        """
        check_universe(universe)
        # check, if the universe already exists in the list:
        if universe in self._outputs:
            return
        # add new output:
        new_output = Output(DataPacket(cid=self.__CID, sourceName=self.source_name, universe=universe))
        self._outputs[universe] = new_output

    def deactivate_output(self, universe: int):
        """
        Deactivates an existing output. Every data from the existing output will be lost. (TTL, Multicast, DMX data, ..)
        :param universe: the universe to deactivate
        """
        check_universe(universe)
        try:
            del self._outputs[universe]
        except:
            pass

    def get_active_outputs(self) -> list:
        """
        Returns a list with all active outputs. Useful when iterating over all sender indexes.
        :return: list: a list with int (every int is a activated universe. May be not sorted)
        """
        return list(self._outputs.keys())

    def move_universe(self, universe_from: int, universe_to: int):
        """
        Moves an output from one universe to another. All settings are being restored and only the universe changes
        :param universe_from: the universe that should be moved
        :param universe_to: the target universe. An existing universe will be overwritten
        """
        check_universe(universe_from)
        check_universe(universe_to)
        # store the output object and change the universe in the packet of the output
        tmp_output = self._outputs[universe_from]
        tmp_output._packet.universe = universe_to
        # deactivate output
        self.deactivate_output(universe_from)
        # activate new output with the new universe
        self._outputs[universe_to] = tmp_output

    def __getitem__(self, item: int) -> Output:
        try:
            return self._outputs[item]
        except:
            return None

    def start(self, bind_address=None, bind_port: int = None, fps: int = None):
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
        self._output_thread = OutputThread(outputs=self._outputs, bind_address=bind_address,
                                           bind_port=bind_port, fps=fps)
        self._output_thread.start()

    def stop(self):
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
        raise TypeError('Universe must be between [1-63999]')
