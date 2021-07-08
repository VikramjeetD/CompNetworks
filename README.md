# File Transfer Protocol Inspired by Selective Repeat in Python

## What is it?
This is an implementation of a reliable file transfer protocol over UDP sockets in python, developed as part of my Computer Networks Course.

## How to use it?
Set all configuration parameters in ```Constants.py```, then set the filepath in ```Server.py```. Finally, run ```$ python Server.py```, followed by ```$ Client.py```.

## How does it do it? (The protocol)
* The protocol builds reliability over UDP sockets
* Each packet has a 9 byte header
    * 4 bytes for sequence number
    * 4 bytes for packet size (While the protocol does not require it since we have a constant header size, it has been kept to help future extensions)
    * 1 byte for packet type (SYN, ACK, DATA, FIN)
    
* To establish the connection, the client sends a SYN packet to the server
* The server consequently sends the packets, expecting an ACK packet for every packet
* UnACKed packets are resent, unless the corresponding ACK is received
* To end the connection, the server sends a FIN and waits for an ACK. It resends it a few times, in case the FIN packet is dropped. The client on receiving the FIN packets sends a few ACKs until it stops receiving duplicate FINs (this means the FINACK maybe dropped). However, it is not possible to make the connection teardown reliable. This however has no impact on the data transfer.

## What situations can it handle?
This protocol has been tested against various combinations of adverse network conditions including packet loss, reordering, delay and jitter using Netem. The protocol is agnostic to packet corruption as that is handled by the UDP layer using checksum.

## How fast does it happen?
| Packet Size (Bytes) 	| Throughput (Mbps) 	|
|---------------------	|-------------------	|
|         2**4        	|       0.314       	|
|         2**5        	|       0.629       	|
|         2**6        	|       1.257       	|
|         2**7        	|       2.503       	|
|         2**8        	|       4.915       	|
|         2**9        	|       9.896       	|
|        2**10        	|       20.391      	|
|        2**11        	|       37.575      	|
|        2**12        	|       59.444      	|
|        2**13        	|       84.164      	|

# What more could have been done?
* The server and client buffer the whole file in memory. This would not be suitable for huge files.
* Support multiple concurrent clients
* Add bidirectional transfer capabilities