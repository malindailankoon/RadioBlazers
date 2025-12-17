# RadioBlazers
Semester 3 "EN2130-Communication Design Project" project files (members: | Kariyawasam JHD (https://github.com/HirunaK) |  Imaduwage ONH (https://github.com/oshan-imaduwage) | Arachchi ADID (https://github.com/isithadinujaya) | Ilankoon IMMKB (https://github.com/malindailankoon))


# Final implementation 
resides at FINAL/aloha_s&p_implementation/

and the important files are:

tx_modified_combined.grc => a combination of user1 and user2 nodes for simulation purposes.

user_1.grc => GNU flowgraph for user 1

user_2.grc => GNU flowgraph for user 2

base_station.grc => the GNU flowgraph for the base station (NOT TESTED)



# Project Objective
Build a Hospital Paging System using SDRs. the system must support transmission of short text messages from one device to another, with proper addressing and acknowledgement mechanisms. 

## core requirements
1. Message delivery: Short message delivery using digital modulation (BPSK/QPSK/etc.).
2.  Unique user addressing: Each receiver must only respond to messages intended for its address or ID.
3. Acknowledgment mechanism (ACK): The receiver must send an acknowledgment upon successful message receipt.
4.  Error Detection: Add CRC-based error detection and discard corrupted messages.
5. Basic User Interface: A simple console- or GUI-based interface to compose and send messages.


# Solution Overview
GNU radio for software and BladeRF 2.0 micro xa4 and xa9 for the hardware

## Topology
The network is a Star Topology with a Base Station and multiple User Nodes. the base station represents a central communication server in the hospital and a user node represents a pager that a doctor would use. the base station can communicate directly with all user nodes but the user nodes can send packets only to the base station. there are two operating frequencies, 900MHz to transmit data from the base station to the users and 3GHz to tramsmit data from the users to the base station. the Base station is capable of not only receiving packets but also forwarding packets that does not address it, allowing all the users to communicate with each other. 


## Design Architecture
our solution consists of 3 Layers of communicaiton:
1. Application Layer (GUI)
2. Data Link Layer (GNU Embedded Python Block and the Protocol Formatter)
3. Physical Layer (Modulation and Demodulation pipelines in the GNU flowgraph)

Our messages are transmitted as packets and an entire message is encapsulated in a variable length packet.


### 1) Application Layer
made using python and the pyqt library. the GUI is implemented as an emmbedded python block to increase speed and reliability but came at the cost of limited customization. this was necessary because we couldn't find any good Inter Process communication methods between an external GUI and GNU flowgraph.


\\ insert image of GUI here






