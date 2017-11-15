## sACN / E1.31 module
---
**BETA!** And therefore currently not in the pypi

This module is a simple sACN library that support the standard DMX message of the protocol.
It is based on the [2016][e1.31] version of the official ANSI E1.31 standard.
It has support for sending out DMX data and receiving it. Multiple and multicast universes are supported.

Currently missing features:
 * discovery messages (receiving and sending)
 * correct stream termination with stream_termination bit (although the most devices are
  not supporting this on the receiver site)

###The Internals
####sending
You can create a new `sACNsender` object and provide the necessary information. Then you have to use `start()`.
This creates a new thread that is responsible for sending out the data. If the data is not changed, the same DMX data
is send out every second.

The thread sends out the data every *1/fps* seconds. This provides synchronization (the data for all universes is send
out the same time) and reduces network traffic even if you give the sender new data more often than the *fps*.
You can tweak this *fps* by simply change it when creating the `sACNsender` object.
####receiving
A very simple solution, as you just create a `sACNreceiver` object and use `start()` a new thread that is running in
the background and calls the callbacks when new sACN data arrives.

---
###Usage
####sending
To use the sending functionality you have to use the `sender.sACNsender`.

```python
import sacn
import time

sender = sacn.sender.sACNsender()  # provide an IP-Address to bind to if you are using Windows and want to use multicast
sender.start()  # start the sending thread
sender.activate_output(1)  # start sending out data in the 1st universe
sender[1].multicast = True  # set multicast to True
# sender[1].destination = "192.168.1.20"  # or provide unicast information.
# Keep in mind that if multicast is on, this is just not used
sender[1].dmx_data = (1, 2, 3, 4)  # some test DMX data

time.sleep(10)  # send the data for 10 seconds
sender.stop()  # do not forget to stop the sender
```

You can activate an output universe via `activate_output(<universe>)` and then change the attributes of this universe
via `sender[<universe>].<attribute>`. To deactivate an output use `deactivate_output(<universe>)`.
Tip: you can get the activated outputs with `get_active_outputs()` and you can move an output with all its settings
from one universe to another with `move_universe(<from>, <to>)`.

Available Attributes are:
 * `destination: str`: the unicast destination as string. (eg "192.168.1.150") Default: "127.0.0.1"
 * `multicast: bool`: set whether to send out via multicast or not. Default: False
 If True the data is send out via multicast and not unicast.
 * `ttl: int`: the time-to-live for the packets that are send out via mutlicast on this universe. Default: 8
 * `priority: int`: the priority for this universe that is send out. If multiple sources in a network are sending to
 the same receiver the data with the highest priority wins. Default: 100
 * `preview_data: bool`: Flag to mark the data as preview data for visualization purposes. Default: False
 * `dmx_data: tuple`: the DMX data as a tuple. Max length is 512 and for legacy devices all data that is smaller than
 512 is merged to a 512 length tuple with 0 as filler value. The values in the tuple have to be [0-511]!

`sender.sACNsender` Creates a sender object. A sender is used to manage multiple sACN universes and handles their output.
DMX data is send out every second, when no data changes. Some changes may be not send out, because the fps
setting defines how often packets are send out to prevent network overuse. So if you change the DMX values too
often in a second they may not all been send. Vary the fps parameter to your needs (Default=30).
Note that a bind address is needed on Windows for sending out multicast packets.
 * `bind_address: str`: the IP-Address to bind to.
 For multicast on a Windows machine this must be set to a proper value otherwise omit.
 * `bind_port: int`: optionally bind to a specific port. Default=5568. It is not recommended to change the port.
 Change the port number if you have trouble with another program or the sACNreceiver blocking the port
 * `source_name: str`: the source name used in the sACN packets. See the [standard][e1.31] for more information.
 * `cid: tuple`: the cid. If not given, a random CID will be generated. See the [standard][e1.31] for more information.
 * `fps: int` the frames per second. See explanation above. Has to be >0.

####receiving
To use the receiving functionality you have to use the `receiver.sACNreceiver`.

```python
import sacn
import time

# provide an IP-Address to bind to if you are using Windows and want to use multicast
receiver = sacn.receiver.sACNreceiver()
receiver.start()  # start the receiving thread

# define a callback function
def callback(packet):  # packet type: sacn.messages.data_packet
    print(packet.dmxData)  # print the received DMX data

receiver.callbacks.append(callback)
# optional: if you want to use multicast use this function with the universe as parameter
receiver.join_multicast(1)

time.sleep(10)  # receive for 10 seconds
receiver.stop()
```

The usage of the receiver is way more simple than the sender.
The `sACNreceiver` can be initalized with the following parameters:
 * `bind_address: str`: if you are on a Windows system and want to use multicast provide a valid interfaceIP-Address!
 Otherwise omit.
 * `bind_port: int`: Default: 5568. It is not recommended to change this value!
 Only use when you are know what you are doing!

Functions:
 * `join_multicast(<universe>)`: joins the multicast group for the specific universe. If you are on Windows you have to
 bind the receiver to a valid IP-Address. That is done in the constructor of a sACNreceiver.
 * `leave_multicast(<universe>)`: leave the multicast group specified by the universe.

####DataPacket
This is an abstract representation of an sACN Data packet that carries the DMX data. This class is used internally by
the module and is used in the callbacks of the receiver.





[e1.31](http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf)