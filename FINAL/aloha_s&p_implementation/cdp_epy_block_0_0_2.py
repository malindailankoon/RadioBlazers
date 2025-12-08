"""
Embedded Python Block for GNU Radio - Mesh Network Packet Communication
Implements packetization, Stop-and-Wait ARQ, and ALOHA collision avoidance
No external CRC module required - implements CRC-16 CCITT manually
"""

import numpy as np
from gnuradio import gr
import pmt
import threading
import queue
import time
import random
import struct

class blk(gr.sync_block):
    """
    Mesh Network Packet Communication Block
    Handles packet transmission/reception with Stop-and-Wait ARQ
    """
    
    def __init__(self, node_id=1, aloha_prob=0.3, timeout=1.0, max_retries=3):
        """
        Arguments:
            node_id: Unique identifier for this node (1-255)
            aloha_prob: Transmission probability for ALOHA (0.0-1.0)
            timeout: ARQ timeout in seconds
            max_retries: Maximum retransmission attempts
        """
        gr.sync_block.__init__(
            self,
            name='Mesh Packet Comm with sync',
            in_sig=None,
            out_sig=None
        )
        
        # Node configuration
        self.node_id = node_id
        self.aloha_prob = aloha_prob
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Packet parameters
        self.PREAMBLE = bytes([0xAA, 0xAA, 0xAA, 0xAA])
        # b = random.getrandbits(8)
        # self.PREAMBLE = bytes([b] * 32)
        self.SYNC_WORD = bytes([0x2D, 0xD4])
        self.MAX_PAYLOAD = 255
        self.HEADER_SIZE = 8  # preamble(4) + sync(2) + src(1) + dst(1)
        self.CRC_SIZE = 2
        
        # Packet types
        self.PKT_DATA = 0x01
        self.PKT_ACK = 0x02
        
        # CRC-16 CCITT lookup table
        self.crc_table = self.generate_crc_table()
        
        # State management
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()
        self.ack_queue = queue.Queue()
        self.pending_ack = {}
        self.seq_num_tx = 0
        self.seq_num_rx = {}
        self.rx_buffer = bytes()
        
        # Statistics
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'acks_sent': 0,
            'acks_received': 0,
            'retransmissions': 0,
            'crc_errors': 0
        }
        
        # Threading
        self.running = True
        self.tx_thread = threading.Thread(target=self.tx_handler)
        self.rx_thread = threading.Thread(target=self.rx_handler)
        self.lock = threading.Lock()
        
        # Message ports
        self.message_port_register_in(pmt.intern('msg_in'))
        self.message_port_register_in(pmt.intern('pdu_in'))
        self.message_port_register_out(pmt.intern('msg_out'))
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.message_port_register_out(pmt.intern('feedback'))
        
        # Set message handlers
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg_in)
        self.set_msg_handler(pmt.intern('pdu_in'), self.handle_pdu_in)
        
        # Start threads
        self.tx_thread.start()
        self.rx_thread.start()
        
        print(f"[Node {self.node_id}] Initialized - Ready for communication")
    
    def generate_crc_table(self):
        """Generate CRC-16 CCITT lookup table"""
        poly = 0x1021
        table = []
        for i in range(256):
            crc = i << 8
            for j in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ poly) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
            table.append(crc)
        return table
    
    def calculate_crc16(self, data):
        """Calculate CRC-16 CCITT for given data"""
        crc = 0xFFFF
        for byte in data:
            tbl_idx = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ self.crc_table[tbl_idx]) & 0xFFFF
        return crc
    
    def handle_msg_in(self, msg):
        """Handle incoming messages from GUI/application"""
        try:
            # Handle string messages directly
            if pmt.is_symbol(msg):
                # Simple text message format: "dst_id:message"
                text = pmt.symbol_to_string(msg)
                if ':' in text:
                    parts = text.split(':', 1)
                    try:
                        dst_id = int(parts[0])
                        data = parts[1].encode()
                        self.tx_queue.put({'dst': dst_id, 'data': data, 'type': self.PKT_DATA})
                        print(f"[Node {self.node_id}] Queued message to {dst_id}: {parts[1]}")
                    except ValueError:
                        print(f"[Node {self.node_id}] Invalid destination ID")
            
            # Handle dictionary messages
            elif pmt.is_dict(msg):
                meta = pmt.to_python(msg)
                if 'dst' in meta and 'data' in meta:
                    dst_id = meta['dst']
                    data = meta['data'].encode() if isinstance(meta['data'], str) else meta['data']
                    self.tx_queue.put({'dst': dst_id, 'data': data, 'type': self.PKT_DATA})
                    print(f"[Node {self.node_id}] Queued message to {dst_id}")
            
            # Handle pair messages (PDU format)
            elif pmt.is_pair(msg):
                meta = pmt.to_python(pmt.car(msg))
                data = pmt.to_python(pmt.cdr(msg))
                if isinstance(meta, dict) and 'dst' in meta:
                    dst_id = meta['dst']
                    if isinstance(data, str):
                        data = data.encode()
                    elif isinstance(data, list):
                        data = bytes(data)
                    self.tx_queue.put({'dst': dst_id, 'data': data, 'type': self.PKT_DATA})
                    print(f"[Node {self.node_id}] Queued message to {dst_id}")
                    
        except Exception as e:
            print(f"[Node {self.node_id}] Error handling msg_in: {e}")
    
    def handle_pdu_in(self, pdu):
        """Handle incoming PDUs from demodulator"""
        try:
            # Extract PDU data
            if pmt.is_pair(pdu):
                meta = pmt.car(pdu)
                data = pmt.cdr(pdu)
                
                # Convert to bytes
                if pmt.is_u8vector(data):
                    print("loop run")	
                    rx_bytes = bytes(pmt.u8vector_elements(data))	
                    self.rx_queue.put(rx_bytes)
                elif pmt.is_uniform_vector(data):
                    # Handle float32 or other vector types
                    elements = pmt.to_python(data)
                    # Convert to bytes (assuming 8-bit symbols)
                    rx_bytes = bytes([int(x) & 0xFF for x in elements])
                    self.rx_queue.put(rx_bytes)
                    
        except Exception as e:
            print(f"[Node {self.node_id}] Error handling pdu_in: {e}")
    
    def create_packet(self, dst_id, seq_num, pkt_type, payload=b''):
        """Create a packet with headers and CRC"""
        packet = bytearray()
        
        # Add preamble and sync word
        packet.extend(self.PREAMBLE)
        packet.extend(self.SYNC_WORD)
        
        # Add header
        packet.append(self.node_id)  # Source ID
        packet.append(dst_id)         # Destination ID
        packet.append(seq_num)        # Sequence number
        packet.append(pkt_type)       # Packet type
        packet.append(len(payload))   # Payload length
        
        # Add payload
        if payload:
            packet.extend(payload[:self.MAX_PAYLOAD])
        
        # Calculate and add CRC16
        crc_data = bytes(packet[len(self.PREAMBLE) + len(self.SYNC_WORD):])
        crc_val = self.calculate_crc16(crc_data)
        packet.extend(struct.pack('>H', crc_val))
        
        return bytes(packet)
    
    def parse_packet(self, data):
        """Parse received packet and validate CRC"""
        try:
            # Find sync word
            sync_idx = data.find(self.SYNC_WORD)
            if sync_idx == -1:
                return None
            
            # Check minimum packet size
            start_idx = sync_idx + len(self.SYNC_WORD)
            if len(data) < start_idx + 5 + self.CRC_SIZE:
                return None
            
            # Extract header fields
            src_id = data[start_idx]
            dst_id = data[start_idx + 1]
            seq_num = data[start_idx + 2]
            pkt_type = data[start_idx + 3]
            payload_len = data[start_idx + 4]
            
            # Check if we have complete packet
            total_len = start_idx + 5 + payload_len + self.CRC_SIZE
            if len(data) < total_len:
                return None
            
            # Extract payload and CRC
            payload = data[start_idx + 5:start_idx + 5 + payload_len]
            rx_crc = struct.unpack('>H', data[total_len - self.CRC_SIZE:total_len])[0]
            
            # Verify CRC
            crc_data = data[start_idx:total_len - self.CRC_SIZE]
            calc_crc = self.calculate_crc16(crc_data)
            
            if rx_crc != calc_crc:
                self.stats['crc_errors'] += 1
                print(f"[Node {self.node_id}] CRC mismatch (expected: {calc_crc:04X}, got: {rx_crc:04X})")
                return None
            
            return {
                'src': src_id,
                'dst': dst_id,
                'seq': seq_num,
                'type': pkt_type,
                'payload': payload,
                'consumed': total_len
            }
        except Exception as e:
            print(f"[Node {self.node_id}] Error parsing packet: {e}")
            return None
    
    def send_sync_burst(self):
        burst = bytes(random.getrandbits(8) for _ in range(1000))
        self.transmit_packet(burst)

    def tx_handler(self):
        """Thread for handling packet transmission with ARQ"""
        while self.running:
            try:
                # Get message from queue (with timeout for thread safety)
                try:
                    msg = self.tx_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # ALOHA: Random backoff
                if random.random() > self.aloha_prob:
                    backoff_time = random.uniform(0.1, 0.5)
                    print(f"[Node {self.node_id}] ALOHA backoff {backoff_time:.2f}s")
                    time.sleep(backoff_time)
                    # Re-queue the message
                    self.tx_queue.put(msg)
                    continue
                
                # Prepare packet
                with self.lock:
                    seq_num = self.seq_num_tx
                    self.seq_num_tx = (self.seq_num_tx + 1) % 256
                
                packet = self.create_packet(
                    msg['dst'],
                    seq_num,
                    msg['type'],
                    msg.get('data', b'')
                )
                
                # Stop-and-Wait ARQ
                retries = 0
                ack_received = False

                self.send_sync_burst()
                
                while retries < self.max_retries and not ack_received:
                    # Transmit packet
                    print(f"[Node {self.node_id}] TX: Sending packet seq={seq_num} to node {msg['dst']} (attempt {retries + 1})")
                    self.transmit_packet(packet)
                    self.stats['packets_sent'] += 1
                    
                    if retries > 0:
                        self.stats['retransmissions'] += 1
                    
                    # Wait for ACK
                    ack_key = f"{msg['dst']}_{seq_num}"
                    timeout_time = time.time() + self.timeout
                    
                    while time.time() < timeout_time:
                        try:
                            ack = self.ack_queue.get(timeout=0.1)
                            if ack['key'] == ack_key:
                                ack_received = True
                                self.stats['acks_received'] += 1
                                print(f"[Node {self.node_id}] TX: ACK received for seq={seq_num}")
                                output = "TRUE"
                                msg = pmt.intern(output)
                                self.message_port_pub(pmt.intern('feedback'), msg)
                                break
                        except queue.Empty:
                            pass
                    
                    if not ack_received:
                        retries += 1
                        if retries < self.max_retries:
                            print(f"[Node {self.node_id}] TX: Timeout, retry {retries}/{self.max_retries}")
                
                if not ack_received:
                    print(f"[Node {self.node_id}] TX: Failed to deliver packet seq={seq_num} after {self.max_retries} attempts")
                    output = "FALSE"
                    msg = pmt.intern(output)
                    self.message_port_pub(pmt.intern('feedback'), msg)
                    
            except Exception as e:
                print(f"[Node {self.node_id}] TX handler error: {e}")
    
    def rx_handler(self):
        """Thread for handling packet reception"""
        while self.running:
            try:
                # Get received data
                try:
                    rx_data = self.rx_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Add to buffer
                self.rx_buffer += rx_data
                
                # Try to parse packets from buffer
                while len(self.rx_buffer) > 0:
                    pkt = self.parse_packet(self.rx_buffer)
                    
                    if pkt is None:
                        # No valid packet found, remove first byte and try again
                        if len(self.rx_buffer) > 1:
                            self.rx_buffer = self.rx_buffer[1:]
                        else:
                            self.rx_buffer = bytes()
                        continue
                    
                    # Remove processed packet from buffer
                    self.rx_buffer = self.rx_buffer[pkt['consumed']:]
                    
                    # Check if packet is for this node or broadcast
                    if pkt['dst'] != self.node_id and pkt['dst'] != 0xFF:
                        print(f"[Node {self.node_id}] RX: Packet not for us (dst={pkt['dst']})")
                        continue
                    
                    # Handle based on packet type
                    if pkt['type'] == self.PKT_DATA:
                        self.stats['packets_received'] += 1
                        print(f"[Node {self.node_id}] RX: Data packet from node {pkt['src']}, seq={pkt['seq']}")
                        
                        # Check for duplicate
                        is_duplicate = False
                        if pkt['src'] in self.seq_num_rx:
                            if self.seq_num_rx[pkt['src']] == pkt['seq']:
                                print(f"[Node {self.node_id}] RX: Duplicate packet detected")
                                is_duplicate = True
                        
                        self.seq_num_rx[pkt['src']] = pkt['seq']
                        
                        # Send ACK
                        ack_packet = self.create_packet(
                            pkt['src'],
                            pkt['seq'],
                            self.PKT_ACK
                        )
                        print(f"[Node {self.node_id}] RX: Sending ACK for seq={pkt['seq']}")
                        self.transmit_packet(ack_packet)
                        self.stats['acks_sent'] += 1
                        
                        # Forward to application if not duplicate
                        if not is_duplicate:
                            self.forward_to_app(pkt['src'], pkt['payload'])
                        
                    elif pkt['type'] == self.PKT_ACK:
                        print(f"[Node {self.node_id}] RX: ACK packet from node {pkt['src']}, seq={pkt['seq']}")
                        # Process ACK
                        ack_key = f"{pkt['src']}_{pkt['seq']}"
                        self.ack_queue.put({'key': ack_key})
                        
            except Exception as e:
                print(f"[Node {self.node_id}] RX handler error: {e}")
    
    def transmit_packet(self, packet):
        """Send packet to physical layer"""
        try:
            # Convert to PDU format
            vec = pmt.init_u8vector(len(packet), list(packet))
            pdu = pmt.cons(pmt.PMT_NIL, vec)
            
            # Send to modulator
            self.message_port_pub(pmt.intern('pdu_out'), pdu)
            
        except Exception as e:
            print(f"[Node {self.node_id}] Error transmitting packet: {e}")
    
    def forward_to_app(self, src_id, data):
        """Forward received data to application/GUI"""
        try:
            # Decode message
            message = data.decode('utf-8', errors='ignore')
            
            # Create formatted output string
            output = f"[From Node {src_id}]: {message}"
            
            # Send as simple string message
            msg = pmt.intern(output)
            self.message_port_pub(pmt.intern('msg_out'), msg)
            
            # Also send as dictionary for more complex processing
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.intern("src"), pmt.from_long(src_id))
            meta = pmt.dict_add(meta, pmt.intern("data"), pmt.intern(message))
            
            print(f"[Node {self.node_id}] Message delivered: {output}")
            
        except Exception as e:
            print(f"[Node {self.node_id}] Error forwarding to app: {e}")
    
    def work(self, input_items, output_items):
        """Main work function (not used for message passing blocks)"""
        return 0
    
    def stop(self):
        """Clean shutdown"""
        print(f"\n[Node {self.node_id}] Statistics:")
        print(f"  Packets sent: {self.stats['packets_sent']}")
        print(f"  Packets received: {self.stats['packets_received']}")
        print(f"  ACKs sent: {self.stats['acks_sent']}")
        print(f"  ACKs received: {self.stats['acks_received']}")
        print(f"  Retransmissions: {self.stats['retransmissions']}")
        print(f"  CRC errors: {self.stats['crc_errors']}")
        
        self.running = False
        if self.tx_thread.is_alive():
            self.tx_thread.join()
        if self.rx_thread.is_alive():
            self.rx_thread.join()
        return True
