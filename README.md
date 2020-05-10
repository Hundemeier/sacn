# sACN / E1.31 module

This module is a simple sACN library that support the standard DMX message of the protocol.
It is based on the [2016][e1.31] version of the official ANSI E1.31 standard.
It has support for sending out DMX data and receiving it. Multiple and multicast universes are supported.
For full blown DMX support use [OLA](http://opendmx.net/index.php/Open_Lighting_Architecture).

Currently missing features:
 * discovery messages (receiving)
 * E1.31 sync feature (on the receiver side)
 * custom ports (because this is not recommended)

Features:
 * out-of-order packet detection like the [E1.31][e1.31] 6.7.2
 * multicast (on Windows this is a bit tricky though)
 * auto flow control (see [The Internals/Sending](#sending))
 * E1.31 sync feature (see manual_flush)

## Setup
This Package is in the [pypi](https://pypi.org/project/sacn/). To install the package use `pip install sacn`. Python 3.6 or newer required!
To use the Libary `import sacn`.
If you want to install directly from source, download or clone the repository and execute `pip install .` where the setup.py is located.
For more information on pip installation see: https://packaging.python.org/tutorials/installing-packages/#installing-from-a-local-src-tree

## The Internals
### Sending
You can create a new `sACNsender` object and provide the necessary information. Then you have to use `start()`.
This creates a new thread that is responsible for sending out the data. Do not forget to `stop()` the thread when
finished! If the data is not changed, the same DMX data is send out every second.

The thread sends out the data every *1/fps* seconds. This reduces network traffic even if you give the sender new data
more often than the *fps*.
A simple description would be to say that the data that you give the sACNsender is subsampled by the *fps*.
You can tweak this *fps* by simply change it when creating the `sACNsender` object.

This function works according to the [E1.31][e1.31]. See 6.6.1 for more information.

Note: Since Version 1.4 there is a manual flush feature available. See Usage/Sending for more info.
This feature also uses the sync feature of the sACN protocol (see page 36 on [E1.31][e1.31]).
Currently this is not implemented like the recommended way (this does not wait before sending out the sync packet), but
it should work on a normal local network without too many latency differences.
When the `flush()` function is called, all data is send out at the same time and immediately a sync packet is send out.

### Receiving
A very simple solution, as you just create a `sACNreceiver` object and use `start()` a new thread that is running in
the background and calls the callbacks when new sACN data arrives.

---
## Usage
### Sending
To use the sending functionality you have to use the `sACNsender`.

```python
import sacn
import time

sender = sacn.sACNsender()  # provide an IP-Address to bind to if you are using Windows and want to use multicast
sender.start()  # start the sending thread
sender.activate_output(1)  # start sending out data in the 1st universe
sender[1].multicast = True  # set multicast to True
# sender[1].destination = "192.168.1.20"  # or provide unicast information.
# Keep in mind that if multicast is on, unicast is not used
sender[1].dmx_data = (1, 2, 3, 4)  # some test DMX data

time.sleep(10)  # send the data for 10 seconds
sender.stop()  # do not forget to stop the sender
```

You can activate an output universe via `activate_output(<universe>)` and then change the attributes of this universe
via `sender[<universe>].<attribute>`. To deactivate an output use `deactivate_output(<universe>)`. The output is
terminated like the [E1.31][e1.31] describes it on page 14.

If you want to flush manually and the sender thread should not send out automatic, use the
`sACNsender.manual_flush` option. This is useful when you want to use a fixture that is using more than one universe
and all the data on multiple universes should send out at the same time.

Tip: you can get the activated outputs with `get_active_outputs()` and you can move an output with all its settings
from one universe to another with `move_universe(<from>, <to>)`.

Available Attributes for `sender[<universe>].<attribute>` are:
 * `destination: str`: the unicast destination as string. (eg "192.168.1.150") Default: "127.0.0.1"
 * `multicast: bool`: set whether to send out via multicast or not. Default: False
 If True the data is send out via multicast and not unicast.
 * `ttl: int`: the time-to-live for the packets that are send out via mutlicast on this universe. Default: 8
 * `priority: int`: (must be between 0-200) the priority for this universe that is send out. If multiple sources in a
 network are sending to the same receiver the data with the highest priority wins. Default: 100
 * `preview_data: bool`: Flag to mark the data as preview data for visualization purposes. Default: False
 * `dmx_data: tuple`: the DMX data as a tuple. Max length is 512 and for legacy devices all data that is smaller than
 512 is merged to a 512 length tuple with 0 as filler value. The values in the tuple have to be [0-255]!

`sACNsender` Creates a sender object. A sender is used to manage multiple sACN universes and handles their output.
DMX data is send out every second, when no data changes. Some changes may be not send out, because the fps
setting defines how often packets are send out to prevent network overuse. So if you change the DMX values too
often in a second they may not all been send. Vary the fps parameter to your needs (Default=30).
Note that a bind address is needed on Windows for sending out multicast packets.
 * `bind_address: str`: the IP-Address to bind to.
 For multicast and universe discovery on a Windows machine this must be set to a proper value otherwise omit.
 * `bind_port: int`: optionally bind to a specific port. Default=5568. It is not recommended to change the port.
 Change the port number if you have trouble with another program or the sACNreceiver blocking the port
 * `source_name: str`: the source name used in the sACN packets. See the [standard][e1.31] for more information.
 * `cid: tuple`: the cid. If not given, a random CID will be generated. See the [standard][e1.31] for more information.
 * `fps: int` the frames per second. See explanation above. Has to be >0. Default: 30
 * `universeDiscovery: bool` if true, universe discovery messages are send out via broadcast every 10s. For this
 feature to function properly on Windows, you have to provide a bind address. Default: True
 * `manual_flush: bool` if set to true, the output-thread will not automatically send out packets. Use the function
  `flush()` to send out all universes. Default: False

When manually flushed, the E1.31 sync feature is used. So all universe data is send out, and after all data was send out
a sync packet is send to all receivers and then they are allowed to display the received data. Note that not all
receiver implemented this feature of the sACN protocol.

Example for the usage of the manual_flush:
```python
import sacn
import time

sender = sacn.sACNsender()
sender.start()
sender.activate_output(1)
sender.activate_output(2)
sender[1].multicast = True # keep in mind that multicast on windows is a bit different
sender[2].multicast = True

sender.manual_flush = True # turning off the automatic sending of packets
sender[1].dmx_data = (1, 2, 3, 4)  # some test DMX data
sender[2].dmx_data = (5, 6, 7, 8)  # by the time we are here, the above data would be already send out,
# if manual_flush would be False. This could cause some jitter
# so instead we are flushing manual
time.sleep(1) # let the sender initalize itself
sender.flush()
sender.manual_flush = False # keep maunal flush off as long as possible, because if it is on, the automatic
# sending of packets is turned off and that is not recommended
sender.stop() # stop sending out
```

### Receiving
To use the receiving functionality you have to use the `sACNreceiver`.

```python
import sacn
import time

# provide an IP-Address to bind to if you are using Windows and want to use multicast
receiver = sacn.sACNreceiver()
receiver.start()  # start the receiving thread

# define a callback function
@receiver.listen_on('universe', universe=1)  # listens on universe 1
def callback(packet):  # packet type: sacn.DataPacket
    print(packet.dmxData)  # print the received DMX data

# optional: if you want to use multicast use this function with the universe as parameter
receiver.join_multicast(1)

time.sleep(10)  # receive for 10 seconds
receiver.stop()
```

The usage of the receiver is way more simple than the sender.
The `sACNreceiver` can be initialized with the following parameters:
 * `bind_address: str`: if you are on a Windows system and want to use multicast provide a valid interfaceIP-Address!
 Otherwise omit.
 * `bind_port: int`: Default: 5568. It is not recommended to change this value!
 Only use when you are know what you are doing!

Please keep in mind to not use the callbacks for time consuming tasks!
If you do this, then the receiver can not react fast enough on incoming messages!

Functions:
 * `join_multicast(<universe>)`: joins the multicast group for the specific universe. If you are on Windows you have to
 bind the receiver to a valid IP-Address. That is done in the constructor of a sACNreceiver.
 * `leave_multicast(<universe>)`: leave the multicast group specified by the universe.
 * `get_possible_universes()`: Returns a tuple with all universes that have sources that are sending out data and this
 data is received by this machine
 * `register_listener(<trigger>, <callback>, **kwargs)`: register a listener for the given trigger.
 You can also use the decorator `listen_on(<trigger>, **kwargs)`. Possible trigger so far:
   * `availability`: gets called when there is no data for a universe anymore or there is now data
   available. This gets also fired if a source terminates a stream via the stream_termination bit.
   The callback should get two arguments: `callback(universe, changed)`
     * `universe: int`: is the universe where the action happened
     * `changed: str`: can be 'timeout' or 'available'
   * `universe`: registers a listener for the given universe. The callback gets only one parameter, the DataPacket.
   You can also use the decorator `@listen_on('universe', universe=<universe>)`.
   The callback should have one argument: `callback(packet)`
     * `packet: DataPacket`: the received DataPacket with all information

### DataPacket
This is an abstract representation of an sACN Data packet that carries the DMX data. This class is used internally by
the module and is used in the callbacks of the receiver.

The DataPacket provides following attributes:
 * `sourceName: str`: a string that is used to identify the source. Only the first 64 bytes are used.
 * `priority: int`: the priority used to manage multiple DMX data on one receiver. [1-200] Default: 100
 * `universe: int`: the universe for the whole message and its DMX data. [1-63999]
 * `sequence: int`: the sequence number. Should increment for every new message and can be used to check for wrong
 order of arriving packets.
 * `option_StreamTerminated: bool`: True if this packet is the last one of the stream for the given universe.
 * `option_PreviewData: bool`: True if this data is for visualization purposes.
 * `dmxData: tuple`: the DMX data as tuple. Max length is 512 and shorter tuples getting normalized to a length of 512.
 Filled with 0 for empty spaces.

### Changelog
 * 1.4.3: The sequence number of the sync-packet when using manual flush was not increased (Thanks to @BlakeGarner ! See #19 for more information)
 * 1.4.2: The internal logging of the receiver_thread and output_thread was using the root logger instead of its module-logger. (Thanks to @mje-nz ! See #18 for more information)
 * 1.4: Added a manual flush feature for sending out all universes at the same time. Thanks to ahodges9 for the idea.


[e1.31]: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
