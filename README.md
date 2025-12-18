# **RadioBlazers — EN2130 Communication Design Project**

This repository contains the full implementation and project files for the **Semester 3 EN2130 Communication Design Project**.  
The goal of the project is to design and build a **hospital paging system** using **GNU Radio** and **BladeRF 2.0 SDRs**, supporting wireless exchange of short text messages with addressing, acknowledgments, and CRC-based error detection.

### **Team Members**
- Kariyawasam JHD — https://github.com/HirunaK  
- Imaduwage ONH — https://github.com/oshan-imaduwage  
- Arachchi ADID — https://github.com/isithadinujaya  
- Ilankoon IMMKB — https://github.com/malindailankoon  

---

# **Final Implementation**
The final working system is located at:

```
FINAL/aloha_s&w_implementation/
```

### Key GNU Radio Flowgraphs
| File | Description |
|---|---|
| `tx_modified_combined.grc` | Combined simulation file containing both User 1 and User 2 nodes (NOT upto date) |
| `user_1.grc` | User Node 1 flowgraph (upto date) |
| `user_2.grc` | User Node 2 flowgraph (upto date) |
| `base_station.grc` | Base Station flowgraph *(not fully tested)* |

---

# **Project Objective**
Design and implement a **Hospital Paging System** using software-defined radios, enabling reliable exchange of short text messages in a multi-user environment.  
The system must support proper addressing, acknowledgment, and error detection.


### Core Requirements
1. **Digital message delivery** using modulation (BPSK/QPSK/etc.)
2. **Unique user addressing** to ensure correct routing
3. **Acknowledgment mechanism** (ACK) for reliability
4. **CRC-based error detection**
5. **Basic user interface** for message composition and viewing

---

# **Solution Overview**
The system is implemented using:
- **GNU Radio** for DSP, networking logic, and flowgraph design
- **BladeRF 2.0 micro (XA4 / XA9)** as the SDR hardware platform

---
# **Network Topology**
The paging network follows a **Star Topology**:

- A **Base Station** acts as the central communication server
- Multiple **User Nodes** function as wireless pagers
- The Base Station can communicate directly with all users
- User Nodes communicate upstream only to the Base Station  
- The Base Station forwards messages to other users as needed

Two operating bands are used:
- **900 MHz**: Base Station → User Nodes (downlink)
- **3 GHz**: User Nodes → Base Station (uplink)

---


# **System Architecture**
Communication is organized into three logical layers:

1. **Application Layer** — GUI messaging interface  
2. **Data Link Layer** — framing, CRC, addressing, ARQ, and ALOHA access  
3. **Physical Layer** — modulation, filtering, synchronization, equalization  

Messages are transmitted as **variable-length packets**, with a limit of **256 characters** per message for simplicity.


<img width="2000" height="885" alt="image" src="https://github.com/user-attachments/assets/1577c2fe-db27-4d32-85b0-e0772094706b" />

---


## **1) Application Layer**
Implemented in **Python + PyQt**, embedded directly into the GNU Radio flowgraph to avoid external IPC overhead.  
This approach improved reliability and timing at the cost of reduced GUI customization flexibility.

<img width="708" height="518" alt="image" src="https://github.com/user-attachments/assets/b1719d75-c9b3-4951-92b2-541be7a37358" />

---


## **2) Data Link Layer**
Responsible for:
- Header generation
- Addressing
- CRC-CCITT-16 error detection
- P-persistent ALOHA medium access
- Stop-and-wait ARQ
- Packet retransmission logic (Base Station forwarding)

The Protocol Formatter adds a synchronization header to PDUs, allowing the receiver to reconstruct packets from a continuous bitstream.

<img width="713" height="224" alt="image" src="https://github.com/user-attachments/assets/11843b95-ab4a-4cfb-ab5d-a4cc69985136" />


### **Frame Structure**
<img width="841" height="371" alt="image" src="https://github.com/user-attachments/assets/07366acc-75cc-41de-a72c-95aba94ff68a" />


### **CRC-CCITT-16**
Provides 16-bit error detection and discards corrupted packets.

### **P-Persistent Style Medium Access**
Packet transmissions follow probability-based collision avoidance.

<img width="286" height="382" alt="image" src="https://github.com/user-attachments/assets/2f33659a-d3ac-4a94-8398-aab5ea5b39ea" />



### **Stop-and-Wait ARQ**
Ensures reliable delivery by requiring acknowledgments after each packet.

<img width="348" height="356" alt="image" src="https://github.com/user-attachments/assets/d06ca2cd-055b-4988-8bd0-4ae62c350da0" />


---

### 3) Physical Layer

<!-- This table is made by Senuda Rathnayake and the credit goes to him -->

| Component | Function | Implementation |
| :--- | :--- | :--- |
| **QPSK Mod/Demod** | Modulates 2 bits/symbol | Rectangular constellation |
| **RRC Pulse Shaping** | Reduces ISI | Polyphase Filter Bank (PFB) |
| **Symbol Sync** | Corrects timing errors | Symbol Sync block |
| **Costas Loop** | Carrier recovery | Phase/freq correction |
| **Adaptive Equalizer (CMA)** | Channel equalization | Linear CMA filter |

---

# **Status**
✔ User nodes tested  
✔ End-to-end messaging implemented  
✔ CRC + ARQ functional  
✔ Addressing functional  
✖ Base station forwarding not fully validated  

---
