# Final Notes:

## 1. Intro/ Overview
```
Bandwidth (bits per second)
Enterpise access networks (Ethernet)
Packet switch:-
'cut through' switch can start transmitting
as soon as it has processed the header
'store and forward' start transmitting 
after received entire packet
End-to-end delay = proc + queue + trans + prop
Throughput (bits/time), bits transferred between sender/ receiver
```
### 1.0 2 forms of switched network:-
**Circuit switching** - <mark>Reserved Resources</mark> (used in the legacy telephone networks) 
	__Why not feasible?__
	1. Inefficient - dedicated circuit cannot be used or shared in periods of silence
	2. Fixed data rate - fixed data rate is not useful
	3. Connection state maintenance - not scalable

**Packet switching** - <mark>On demand allocation</mark> (used in the internet)
	Data is sent as chunks of formatted bits (packets, it consists of a 'header' and 'payload')
	switches 'forward' packets based on header
	No link resources reserved, leverages **statistical multiplexing**
	More users to use network, Great for bursty network but excessive congestion (packet delay and loss) 

### 1.1 Loss and Delay
Packet arrival rate to link exceeds output link capacity
Packets queue and wait for turn
1. d<sub>processing</sub> ~> checks bit errors, determine output link
2. d<sub>queueing</sub> ~> time wait at output link, dependant on congestion level of router
3. d<sub>tansmission</sub> ~> L(packet length) / R(link bandwidth)
4. d<sub>propagation</sub> ~> d(length of physical link) / s(propagation speed)

d<sub>end-to-end</sub> = d<sub>processing</sub> + d<sub>queueing</sub> + d<sub>tansmission</sub> +  d<sub>propagation</sub>

### 1.2 Throughput
<mark>_instantaneous_</mark>: rate at given point in time
<mark>_average_</mark>: rate over longer period of time
Bottleneck link ~> link on end-to-end path that constrains end-to-end throughput
In practice, R<sub>server</sub> or R<sub>client</sub> is bottleneck

## 2. Application Layer
```
Uniform Resource Locator(URL)
Hypertext transfer protocol (HTTP) - uses TCP and stateless
```
_identifier_ includes *IP address* and *Port numbers* associated
example port numbers:
- HTTP server: 80
- mail server: 25
- ssh: 22

| Server | Client |
|--|--|
| Always-on host | Intermittently connected |
| Permanent IP | Dynamic IP |
| May communicate with other servers | Don't communicate directly with each other |

### 2.0 App - layer protocol defines
- types of messages exchanged (response, request)
- message syntax
- message semantics
- rules
- open protocols
- proprietary protocols

### 2.1 Performance of HTTP
- Page Load Time (PLT) 
	- key measure of web performance
- Depends on
	1. page content/ structure
	2. protocols involved
	3. bandwidth and RTT
- <mark>NEW TCP connection per object!</mark>

### 2.2 Non-Persistent HTTP
- One object sent over TCP connection then close
- Multiple objects required multiple connections
- One RTT to initiate TCP connection + One RTT for HTTP request + file transmission time
<mark>**response time = 2RTT + file trans time**</mark>

### 2.3 Persistent HTTP
1. **without pipelining**
	- client issue new request after response received
	- <mark>one RTT for each referenced object</mark>
2. **with pipelining**
	- client send requests as soon as referenced object encountered
	- <mark>as little as one RTT for all referenced object</mark>

### 2.4 Caching
- Exploits *locality* of reference

**Web caches (proxy server)**
- satisfy client request without involving origin server
- acts as both client and server
	- client to origin server
	- server for requesting client
 
 ### 2.5 Content Distribution Network (CDN)
Caching and replication as a service
- **Pull**(caching): Direct results of clients' requests
- **Push**(replication): Expectation of high access rate 

### 2.6 HTTPS
HTTP is insecure, uses base64 encoding
HTTPS is HTTP over a connection encrypted by Transport Layer Security (TLS)

| HTTP | SMTP |
|--|--|
| pull | push |
| each object encapsulated in own response msg | multiple objects sent in multipart msg |

### 2.7 Domain Name System (DNS)
- **distributed database** implemented in hierarchy of many **name servers**
- **App-Layer protocol**
hosts, name server communicate to **resolve** names(address/ name translation)

**Hierarchy**
- Hierarchical namesapce
- Hierarchically administered
- Hierarchy of servers
**Top Level Domain TLD**
- top level country domains, .com .org etc
**Authoritative DNS server**
- organization's won DNS server, providing authoritative hostname to IP for organization's host
**Local DNS name server**
- each ISP has one (default name server)

**DNS name resolution**
1. **Iterated query**
- contacted server replies with name of server to contact

| No. | From | To |
|--|--|--|
| 1 | Host<sub>requesting</sub> | local DNS server |
| 2 | local DNS server | root DNS server |
| 3 | root DNS server | local DNS server |
| 4 | local DNS server | TLD DNS server |
| 5 | TLD DNS server | local DNS server |
| 6 | local DNS server | authoritative DNS server |
| 7 | authoritative DNS server | local DNS server |
| 8 | local DNS server | Host<sub>requesting</sub> |
2. **Recursive query**
- puts burden of name resolution on contacted server

| No. | From | To |
|--|--|--|
| 1 | Host<sub>requesting</sub> | local DNS server |
| 2 | local DNS server | root DNS server |
| 3 | root DNS server | TLD DNS server |
| 4 | TLD DNS server | authoritative DNS server |
| 5 | authoritative DNS server | TLD DNS server |
| 6 | TLD DNS server | root DNS server |
| 7 | root DNS server | local DNS server |
| 8 | local DNS server | Host<sub>requesting</sub> |

**DNS records**
1. **type=A**
name: hostname
value: IP address
2. **type=NS**
name: domain
value: authoritative name server for the domain
3. **type=CNAME**
name: alias for some canonical (real) name
value: canonical name
4. **type=MX**
value: name of mailserver associated 

**Attacking DNS**
1. **DDoS attacks**
Bombard root server with traffic
2. **Redirect attacks**
Intercept queries
DNS cache poisoning - send bogus replies to DNS server which caches
3. **Exploit DNS for DDoS**
Send queries with spoofed source address
Requires amplification

## 3. Network Layer
Find paths through network (routing from one end host to another)

**Doesn't**
1. Reliable transfer
2. Guarantee paths
3. Arbitrate transfer rates

### 3.0 Multiplexing / Demultiplexing
<mark>**multiplexing at sender**</mark>
Handles data from multiple sockets and add transport header
<mark>**demultiplexing at receiver**</mark>
Header info is used to deliver received segments to the correct socket

### 3.1 UDP
- connectionless
	- no handshaking
	- each UDP segment handled independently of others
- "best effort" service, UDP segments maybe **lost** or **delivered out of order**
- small header size
- no congestion control: blast away as fast as desired

**UDP checksum**
detect "errors"
1. router memory errors
2. drivers bugs
3. electromagnetic interference

**Bad things about best-effort**
- packet is corrupted
- packet is lost
- packet delayed
- packets are reordered
- packet is duplicated

**Principles of reliable data transfer**
<mark>Stop and wait</mark> -> sender sends one packet, then waits for receiver response

rdt1.0: reliable transfer over a reliable channel
- no bits errors
- no loss
- Transport layer does nothing

rdt2.0: channel with bit errors
- checksum to detect bit errors
- **acknowledgements (ACKs)**: receiver explicitly tells sender that packet received OK
- **negative acknowledgements (NACKs)**: receiver explicitly tells sender that packet had errors, then sender retransmits packet on receipt of NACK

rdt2.1: discussion
| sender | receiver |
|--|--|
| -sequence # added to packet (0,1) | -check if received duplicate (0,1) indicates whether is expected packet seq # |
**NoTe: receiver can not know if its last ACK or NACK received OK at sender**

rdt2.2: NACK free protocol
- same as rdt2.1 but using only ACK
- receiver sends ACK with seq # of packet

rdt3.0: channels with errors and loss
U<sub>sender</sub> = (L/R) / (RTT + L/R)

### 3.2 Pipelined protocols
- pipelining: sender allows multiple, <mark>yet-to-be-acknowledged packets</mark>

**2 generic forms of pipelined**
| go-Back-N (GBN) | selective repeat (SR) |
| -- | -- |
| sender can have upto N unacked packets in pipeline | '' |
| single timer for oldest packet, retransmit all packets when expire | timer for all packets, retranmist only packet where timer expire |
| no buffer at receiver, out of order packet discarded | receiver has buffer, can accept out of order packets |
| receiver send cumulative ack, if gap doesn't ack packet | receiver sends individual ack |

*N is number of packet
U<sub>sender</sub> = (N * L/R) / (RTT + L/R)

### 3.3 Recap: components of a solution
- checksims (error detection)
- timers (loss detection)
- acknowledgements
	1. cumulative 
	2. selective
- Seq # (duplicates, windows)
- Sliding windows (efficiency)
	1. Go-Back-N (GBN)
	2. Selective Repeat (SR)

### 3.4 TCP
- pipelined: congestion and flow control set window size
- MSS: maximum segment size
- piggybacking : (without: ACK then response), (with: ACK + response)

**IP packet**
- maximum transimission unit (MTU) : 1500 bytes with ethernet

**TCP packet**
- TCP header >= 20 bytes long

**TCP segment**
- no more than MSS, upto 1460 bytes from stream
- MSS = MTU - 20 * (min IP header) - 20 * (min TCP header)

**TCP timeout**
- longer than RTT but RTT varies
- too short, premature timeout, unnecessary retransmissions
- too long, slow reaction to segments loss and connection has lower throughput

**estimateRTT**
- average several recent measurements, not just current <mark>sampleRTT</mark>
- <mark>sampleRTT</mark>: meausre time from segment transmission till ACK receipt, ignore retransmissions

**TCP round trip time, timeout**
- RTT<sub>Estimated</sub> = (1 - a) * RTT<sub>Estimated</sub> + a * RTT<sub>sample</sub>
- Timeout Interval = RTT<sub>estimated</sub> + 4 * RTT<sub>dev</sub>

**TCP flow control**
- receiver controls sender, sp sender won't overflow receiver's buffer by tranmitting
- too much or too fast

**TCP SYN Attack (SYN flooding)**
- fake SYN packet, large number can overwhelm victim
- ACK never comes
- Solution
	1. increase size of connection queue
	2. Decrease timeout wait for 3 way handshake
	3. Firewalls: list of known bad source IP addr
	4. TCP SYN cookies

**TCP SYN Cookie**
- on receipt of SYN, server does not create connection
- creates initial sequence number that us a hash of source & destination IP and port of SYN packet (secret key used for hash)
- if fake SYN, no harm since no state created

### 3.5 Principles of congestion control
**Congestion**: too many sources sending too much data too fast for *network* to handle
<mark>Not the same as flow control</mark>
**congestion causes:**
1. lost packets ~> buffer overflow at routers
2. long delays ~> queueing in router buffers

**without congestion control**
1. increase delivery latency
	- variable delays
	- if delays > recovery time objective, sender retransmitted
2. Increase loss rate
	- dropped packets are retransmitted
3. Increases retransmission, many unnecassary
	- wastes capacity of traffic that is never delivered
	- increase load results and decrease in useful work done
4. Increases congestion

**cost of congestion**
1. knee
	- throughput increases slowly
	- delay increases fast
2. Cliff
	- throughput starts to drop to zero
	- delay approaches infinity

**2 broad approaches towards congestion control**
1. end-end congestion control
- no explicit feedback from network
- congestion inferred from end system observed loss, delay
- taken by tcp 
2. network-assisted congestion control
- routers provide feedback to end systems

**TCP's approach**
TCP connection has window, which controls number of packets in flight
TCP sending rate:
rate = CWND / RTT
<mark>**CWND: congestion window**
**RWND: advertised/ receive window (flow control window)**</mark>

### 3.6 Losses
- Duplicate ACKs: isolated loss (network capable of delivering some segments)
- Timeout: much more serious (not enough dup ACKs, must have suffered several losses)

### 3.7 Rate adjustment
Basic structure: either <mark>upon receipt of ACK, increase rate</mark> or <mark>upon detection of loss: decrease rate</mark>
Increase / decrease rate depends on phase of congestion control either <mark>discovering available bottleneck bandwidth</mark> or <mark>adjusting to badnwidth variations</mark>

### 3.8 TCP slow start (Bandwidth discovery)
when connection begins **increase rate exponentially** until **first loss event**

*double CWND every RTT (full ACKs)
*simple, incrementing CWND for every ACK received

TCP uses: Additive Increase Multiplicative Decrease (AIMD)
**additive increase:** increase CWND by 1 MSS every RTT till loss
**multiplicative decrease:** cut CWND in half after loss

*slow start threshold
sender stop Slow-start and start Additive increase: when CWND == ssthresh
- on timeout, ssthresh = CWND / 2

**EVENTS**
- ACK (new data): if CWND < ssthresh(slo w start), CWND += 1 else(congestion avoidance), CWND = CWND + 1 / CWND
- dupACK (dup ACK for old data): dupACKcount ++, if dupACKcount = 3, ssthrest = CWND / 2 and CWND = CWND / 2
- timeout: ssthresh = CWND / 2 and CWND = 1

**Fast Recovery (improved)**
- grant sender temporary credit for each dupACK to keep packets in flight
**while in fast recovery**, CWND = CWND + 1 for each additional dup ACK
**Exit fast recovery after receiving new ACK**, CWND = ssthresh

**TCP-Tahoe**: CWND = 1 on triple dup ACK & timeout
**TCP-Reno**: CWND = 1 on timeout, CWND = CWND / 2 on triple dup ACK
**TCP-newReno**: TCP-Reno + improve fast recovery

**TCP fairness**: if k TCP sessions share same bottleneck link of bandwidth R, each should have average rate of R / K

**Why AIMD**, rate adjustment options: Every RTT we can Multiplicative increase or decrease and Additive increase or decrease
- AIAD: gentle increase, gentle decrease (not converge to fairness)
- AIMD: gentle increase, drastic decrease (converge to fairness)
- MIAD: drastic increase, gentle decrease
- MIMD: drastic increase, drastic decrease

## 4.0 Network Layer
- transport segment from sending to receiving host
- host<sub>sending</sub> encapsulates segments into datagrams
- host<sub>receiving</sub> delivers segments to transport layer

### 4.1 two key network layer functions
1. forwarding (forwarding table) : move packets from router's input to appropriate router output
2. routing (end-end path) : determine route taken by packets from source to dest

**Data plane**
- local, per router function
- determines how datagram arriving on router input port is forwarded to router output port

**Control plane**
- network-wide logic
- determines how datagram is routed among routers along end-end path from host<sub>source</sub> to host<sub>destination</sub>
- 2 approaches
	- traditional routing algo
	- software-defined networking (SDN)

**Potential problems**
Loop: Time To Live(TTL)
- forwarding loops cause packets to cycle for a long time, will eventually consume all capacity
- TTL field (8 - bits): decrements at each hop, packet discarded if reaches 0, then "time exceeded" message sent to source

Header corrupted: Checksum
- if incorrect, router discards packets
- checksum recalculated at every router

Packet too large: Fragmentation
- network links have MTU (max transmission size)
- one datagram becomes several datagrams, resembles only at final destination then IP header bits used to identity and order related fragments

### 4.2 IPv4 fragmentation procedure
<mark>fragmentation of fragments also supported</mark>
- fragmentation
	- router breaks up datagrams in size the output link can support
	- copies IP header to pieces
	- adjust length on pieces
	- set offset to indicate position
	- set MF(more fragments) flag on pieces except the last
	- re-compute checksum
- Re-assembly
	- host<sub>receiving</sub> uses identification field with MF and offsets to complete the datagram

if host<sub>source</sub> sends large packet and set DF (Do not fragment) flag, router will drop packet if too large since DF is set, and send feedback to host<sub>source</sub>

**Special handling**
- "type of service" or "differentiated services code point" (DSCP)
	- packets to be treated differently based on needs
- options (not often used)

### 4.3 IP addressing
IP addr: 32 bits
interface: connection between host/ router and physical link
**Host** has one or two interfaces (wired Ethernet or wireless 802.11)
**Router** have multiple interfaces

IP addr: network part (high order bits), host part (low order bits)
Network is device interfaces with same network part of IP addr and can physically reach each other without intervening router

| Host | decimal addr | Binary |
|--|--|--|
| IP addr | 223.1.1.2 | 11111101 00000001 00000001 0000010 |
| Mask | 255.255.255.0 | 11111111 11111111 11111111 00000000 |
| Network Part | 223.1.1.0 | 11111101 00000001 00000001 00000000 |
| Host Part | 0.0.0.2 | 00000000 00000000 00000000 00000010|

Mask: used in conjunction with network addr to indicate how many higher order bits are used for network part

**Original Internet addr**
- first eight bits: network addr ()
- last 24 bits: host addr, ~16.7 million

*network comes in 3 sizes
| Class | netid | hostid |
|--|--|--|
| A | 2<sup>7</sup> | 2<sup>24</sup> |
| B | 2<sup>14</sup> | 2<sup>16</sup> |
| C | 2<sup>21</sup> | 2<sup>8</sup> |

**Subnetting**
- sacrificing host ID bits to gain Network ID bits

**CIDR Classless InterDomain Routing**
addr format: a.b.c.d/x, where x is # bits in network portion of addr 

**DHCP Dynamic Host Configuration Protocol**
- dynamically get address from as server
- can return
	- addr of first-hop router for client
	- name and IP addr of DNS server
	- network mask
- uses UDP and port 67 (server) and 68 (client)

**Hierarchical addressing: route aggregation**
- allows efficient advertisement of routing info

**IP addr**
- allocated as blocks and have geographical significance
- it is possible to determine the geographical location of an IP
- ISP get block of addr by ICANN Internet corporation for Assigned Names and Numbers

### 4.4 NAT Network Address Translation
NAT router must 
- *outgoing datagrams*: replace (source IP addr, port #) of every outgoing datagram to (NAT IP address, new port #), remote clients/ servers will respond using (NAT IP address, new port #) as destination addr 
- **NAT translation table** every (source IP addr, port #) to (NAT IP addr, new port #) translation pair
- *incoming datagrams*: replace (NAT IP addr, new port #) in destination field of every incoming datagram with corresponding (source IP address, port #) in NAT table

| Advantages | Disadvantages |
|--|--|
| one IP addr for all devices | violates architectural model of IP |
| change addrs of devices in local network without notifying outside world | change internet from connectionless to a connection oriented network |
|can change ISP without changing addrs od devices in local network | requires recalculation of TCP and IP checksum |

### 4.5 Internet Routing
- intra-domain (within domain)
	- link state
	- distance vector
- inter-domain (between domain)
	- path vector

**Link cost**
- all links are equal
- least-cost paths ~> shortest paths by hop count

| Link state (Global) | Distance vector (Decentralised) |
|--|--|
| routers maintain cost of each link | routers maintain next hop & cost of each destination |
| connectivity/ cost changes flooded to all routers | connectivity/ cost changes iteratively propagate from neighbour to neighbour |
| converges quickly (less inconsistency, looping) | requires multiple rounds to converge |
| limited network sizes | scales to large networks |

**Link State routing**
- node maintains local link state
- node floods local link state
- **challenges**: packet loss and out of order
- **solutions**: ACK and retransmissions, seq # and time-to-live for each packet
- **dijkstra**
	- c(x, y) link cost from x to y, inf if not direct neigbors
	- D(v) current value of cost from source to dest
	- p(v) predecessor ode along path from source to v
	- N' set of nodes whose least cost path def known
	**Scalability Issue**
	- O(N * E), N is # nodes, E is # edges (flood link state messages)
	- processing complexity O(N<sup>2</sup>), O(N) iterations
	- O(E) entries in Link State topology database
	- O(N) entries in forwarding table
	**Transient disruptions**
	- inconsistent link state db cause transient forwarding loops

**Distance vector algo**
let d<sub>x</sub>(y) = least cost path from x to y
then d<sub>x</sub>(y) = min {c(x,v) + d<sub>v</sub>(y)}

**iterative, asynchronous** link cost change, DV update message from neighbor
**distributed** notifies neighbour only when DV changes
- message complexity, convergence time varies
- speed of convergence, may be routing loops, coute-to-infinity problem

Robustness, what happens if router malfunctions
| LS | DV |
|--|--|
| advertise incorrect link cost | advertise incorrect path cost |
| computes only own table | error propagate thru network |

## 5.0 Link layer
- focus within a subnet
- data-link layer has responsibility of transferring datagram from one node to physically adjacent node over a link

**framing, link access**
- encapsulate datagram into frame, adding header and trailer
- "MAC" addr used in frame headers to identify source and destination
- implemented in <mark>adaptor (network interface card NIC)</mark>

**reliable delivery between adjacent nodes**
- wireless links, high error rates

**flow control**: pacing between adjacent sending and receiving nodes
**error detection not 100% realiable**: caused by signal attenuation, noise, receiver detects errors and signal sender for retransmission or drop frame
**error correction**: receiver identifies and correct bit errors without retransmission
**half-duplex and full-duplex**: if half, both end of link can transmit but not at the same time

### 5.1 mutiple access link
- point to point
	- PPP for dial up access
	- point to point link between ethernet switch, host
- broadcast (shared wire or medium)
	- old fashioned ethernet
	- upstream HFC
	- 802.11 wireless LAN

**multiple access protocols**
- single shared broadcast channel
- collision if simultaneous transmissions
- determine when node can tranmit

**MAC protocol**
- channel partioning (time division, frequency division)
- random access (dynamic)
- taking turns (polling)

### 5.2 MAC address and ARP
- 32 bit IP addr (network layer addr for interface)

MAC (or LAN ir physical or Ethernet) address
- use locally to get frame from one interface to another physically connected interface (same network)
- 48 bit MAC addr (most LAN) burned in NIC ROM

**LAN addr**
- MAC addr allocation administered by IEEE
- manufacturer buys portion of MAC addr space (ensure uniqueness)
- MAC flat addr portability: can move LAN card from one to another
- IP hierarchical addr not portable: depends on IP subnet to which node is attached

| MAC addr | IP addr |
|--|--|
| hard coded | configured |
| Flat name space 48 bits | Hierarchical name space 32 bits |
| portable | not portable |
| used to get packet between interfaces on same network | used to get packet to destination IP subnet |

**ARP address resolution protocol**
ARP table, each IP on LAN has IP / MAC addr mappings for some LAN node and TTL time after which addr mapping will be forgotten 

### 5.3 Ethernet
- ethernet frame structure, addr (6 byte source, destination MAC addr)
- connectionless (no handshaking)
- unreliable (receiving NIC does not send ACKS or NACKS to sending NIC)
- MAC protocol: unslotted CSMA/CD with binary backoff

**Ethernet switch**
- link layer device
- transparent (hosts are unaware of presence of switches)
- plug and play, self learning (switches do not need to be configured)
- can transmit simultaneously without collisions

**store and forward**
| router | switch |
|--|--|
| network layer devices | link layer devices |

**forwarding table**
| router | switch |
|--|--|
| using routing algo and IP addr | using flooding, learning, MAC addr |

**Issues**
- once switch table entries are established frames are not broadcast
- switch poisoning: attacker fills switch table with bogus entries by large # of frames with bogus source MAC addr
- full switch table, genuine packets frquently need to broadcast as previous entries wiped out

## 6.0 Wireless Network
**wireless link differences from wired link**
- decreased signal strength (radio signal attenuates as it propagates)
- interferences from other sources: standardized wireless network frequencies
- multipath propagation (radio signal reflects off objects ground, arriving at dest at slightly different times)

*distance = d
*lambda = wavelength
*frequency = f
*speed of light = c
Free Space Path Loss 
= ((4 * Pi * d) / lambda )<sup>2</sup>
or
= ((4 * Pi * d * f) / c )<sup>2</sup>

**802.11 LAN architecture**
- wireless host communicates with base station (access point)
- Basic Service Set (BSS) aka cell in infrastructure mode
- hots must **assocuate** with an AP

**passive scanning**
- 1 frames sent from APs
- association request frame sent to selected AP
- association response frame sent from selected AP

**active scanning**
- probe request frame broadcast from client
- prove response frame sent from APs
- association request frame sent to selected AP
- association response frame sent from selected AP

**Multiple access**
- no concept of global collision (different receiver hear different signals, different sender reach different receivers)
- collisions are at receiver, not sender
- protocol is to detect if receiver can hear sender, tells sender who might interfere with receiver to shut up
