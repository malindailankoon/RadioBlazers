"""
Embedded Python Block for GNU Radio - Mesh Network Packet Communication
Implements packetization, Go-Back-N ARQ, and p-persistent ALOHA medium access
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
import collections


class blk(gr.sync_block):
    """
    Mesh Network Packet Communication Block
    Handles packet transmission/reception with Go-Back-N ARQ + ALOHA
    """

    def __init__(
        self,
        node_id = 1,
        aloha_prob = 0.3,
        timeout = 1.0,
        max_retries = 3,
        window_size = 4,
        aloha_backoff_min = 0.1,
        aloha_backoff_max = 0.5,
    ):
        """
        Arguments:
            node_id:           Unique identifier for this node (1-255)
            aloha_prob:        Transmission probability (p) for p-persistent ALOHA (0.0-1.0)
            timeout:           ARQ timeout in seconds (timer for base of window)
            max_retries:       Maximum window retransmission attempts before giving up
            window_size:       Go-Back-N window size (number of outstanding frames)
            aloha_backoff_min: Minimum backoff before (re)transmission when ALOHA defers
            aloha_backoff_max: Maximum backoff before (re)transmission when ALOHA defers
        """
        gr.sync_block.__init__(
            self,
            name='Mesh Packet Comm GBN',
            in_sig=None,
            out_sig=None
        )

        # Node configuration
        self.node_id = node_id
        self.aloha_prob = float(aloha_prob)
        self.timeout = float(timeout)
        self.max_retries = int(max_retries)
        self.window_size = int(window_size)
        self.aloha_backoff_min = float(aloha_backoff_min)
        self.aloha_backoff_max = float(aloha_backoff_max)

        # Packet parameters
        # Preamble: long, random-ish pattern for sync
        b = random.getrandbits(8)
        self.PREAMBLE = bytes([b] * 32)
        self.SYNC_WORD = bytes([0x2D, 0xD4])
        self.MAX_PAYLOAD = 255
        self.CRC_SIZE = 2

        # Packet types
        self.PKT_DATA = 0x01
        self.PKT_ACK = 0x02

        # CRC-16 CCITT lookup table
        self.crc_table = self.generate_crc_table()

        # Queues
        self.tx_queue = queue.Queue()   # app -> link layer (messages to send)
        self.rx_queue = queue.Queue()   # PHY -> link layer (raw received bytes)
        self.ack_queue = queue.Queue()  # RX thread -> TX thread (parsed ACKs)

        # TX state (Go-Back-N)
        self.seq_num_tx = 0  # next sequence number to use (mod 256)
        # window: OrderedDict[seq] = {
        #   'packet': bytes,
        #   'feedback_sent': bool
        # }
        self.tx_window = collections.OrderedDict()
        self.window_timer_start = None
        self.window_retries = 0

        # RX state (per-source expected sequence for GBN)
        # expected_seq_rx[src_id] = next expected seq from that source
        self.expected_seq_rx = {}

        # RX byte buffer for packet extraction
        self.rx_buffer = bytes()

        # Statistics
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'acks_sent': 0,
            'acks_received': 0,
            'retransmissions': 0,
            'crc_errors': 0,
            'window_timeouts': 0,
        }

        # Threading
        self.running = True
        self.tx_thread = threading.Thread(target=self.tx_handler)
        self.rx_thread = threading.Thread(target=self.rx_handler)
        self.tx_thread.daemon = True
        self.rx_thread.daemon = True

        # Message ports
        self.port_msg_in = pmt.intern('msg_in')
        self.port_pdu_in = pmt.intern('pdu_in')
        self.port_msg_out = pmt.intern('msg_out')
        self.port_pdu_out = pmt.intern('pdu_out')
        self.port_feedback = pmt.intern('feedback')

        self.message_port_register_in(self.port_msg_in)
        self.message_port_register_in(self.port_pdu_in)
        self.message_port_register_out(self.port_msg_out)
        self.message_port_register_out(self.port_pdu_out)
        self.message_port_register_out(self.port_feedback)

        # Set message handlers
        self.set_msg_handler(self.port_msg_in, self.handle_msg_in)
        self.set_msg_handler(self.port_pdu_in, self.handle_pdu_in)

        # Start threads
        self.tx_thread.start()
        self.rx_thread.start()

        print(f"[Node {self.node_id}] Initialized (GBN+ALOHA) - Ready for communication")

    # -------------------------------------------------------------------------
    # CRC helpers
    # -------------------------------------------------------------------------
    def generate_crc_table(self):
        """Generate CRC-16 CCITT lookup table"""
        poly = 0x1021
        table = []
        for i in range(256):
            crc = i << 8
            for _ in range(8):
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

    # -------------------------------------------------------------------------
    # Upper-layer message handling
    # -------------------------------------------------------------------------
    def handle_msg_in(self, msg):
        """Handle incoming messages from GUI/application"""
        try:
            # Handle string messages directly: "dst_id:message"
            if pmt.is_symbol(msg):
                text = pmt.symbol_to_string(msg)
                if ':' in text:
                    dst_str, payload_str = text.split(':', 1)
                    try:
                        dst_id = int(dst_str)
                        data = payload_str.encode()
                        self.tx_queue.put({'dst': dst_id, 'data': data, 'type': self.PKT_DATA})
                        print(f"[Node {self.node_id}] Queued message to {dst_id}: {payload_str}")
                    except ValueError:
                        print(f"[Node {self.node_id}] Invalid destination ID in text message")

            # Handle dictionary messages (Python dict via pmt.to_python)
            elif pmt.is_dict(msg):
                meta = pmt.to_python(msg)
                if 'dst' in meta and 'data' in meta:
                    dst_id = meta['dst']
                    data = meta['data'].encode() if isinstance(meta['data'], str) else meta['data']
                    self.tx_queue.put({'dst': dst_id, 'data': data, 'type': self.PKT_DATA})
                    print(f"[Node {self.node_id}] Queued dict message to {dst_id}")

            # Handle PDU-style pair: (meta, vec)
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
                    print(f"[Node {self.node_id}] Queued PDU message to {dst_id}")

        except Exception as e:
            print(f"[Node {self.node_id}] Error handling msg_in: {e}")

    def handle_pdu_in(self, pdu):
        """Handle incoming PDUs from demodulator/PHY"""
        try:
            if not pmt.is_pair(pdu):
                return

            meta = pmt.car(pdu)
            data = pmt.cdr(pdu)

            if pmt.is_u8vector(data):
                rx_bytes = bytes(pmt.u8vector_elements(data))
                self.rx_queue.put(rx_bytes)
            elif pmt.is_uniform_vector(data):
                elements = pmt.to_python(data)
                rx_bytes = bytes([int(x) & 0xFF for x in elements])
                self.rx_queue.put(rx_bytes)

        except Exception as e:
            print(f"[Node {self.node_id}] Error handling pdu_in: {e}")

    # -------------------------------------------------------------------------
    # Packet creation & parsing
    # -------------------------------------------------------------------------
    def create_packet(self, dst_id, seq_num, pkt_type, payload=b''):
        """Create a packet with headers and CRC"""
        packet = bytearray()

        # Preamble + sync
        packet.extend(self.PREAMBLE)
        packet.extend(self.SYNC_WORD)

        # Header
        packet.append(self.node_id)        # Source ID
        packet.append(dst_id & 0xFF)       # Destination ID
        packet.append(seq_num & 0xFF)      # Sequence number
        packet.append(pkt_type & 0xFF)     # Packet type
        packet.append(len(payload) & 0xFF) # Payload length

        # Payload (truncated to MAX_PAYLOAD)
        if payload:
            packet.extend(payload[:self.MAX_PAYLOAD])

        # CRC over header + payload (not including preamble+sync)
        crc_data = bytes(packet[len(self.PREAMBLE) + len(self.SYNC_WORD):])
        crc_val = self.calculate_crc16(crc_data)
        packet.extend(struct.pack('>H', crc_val))

        return bytes(packet)

    def parse_packet(self, data):
        """Parse received packet and validate CRC. Returns dict or None."""
        try:
            # Find sync word
            sync_idx = data.find(self.SYNC_WORD)
            if sync_idx == -1:
                return None

            start_idx = sync_idx + len(self.SYNC_WORD)

            # Minimum: src(1) + dst(1) + seq(1) + type(1) + len(1) + CRC(2)
            if len(data) < start_idx + 5 + self.CRC_SIZE:
                return None

            src_id = data[start_idx]
            dst_id = data[start_idx + 1]
            seq_num = data[start_idx + 2]
            pkt_type = data[start_idx + 3]
            payload_len = data[start_idx + 4]

            total_len = start_idx + 5 + payload_len + self.CRC_SIZE
            if len(data) < total_len:
                return None

            payload = data[start_idx + 5:start_idx + 5 + payload_len]
            rx_crc = struct.unpack('>H', data[total_len - self.CRC_SIZE:total_len])[0]

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

    # -------------------------------------------------------------------------
    # Medium access (ALOHA) + physical transmit
    # -------------------------------------------------------------------------
    def send_with_aloha(self, packet):
        """
        Apply simple p-persistent ALOHA:
        - With probability p = aloha_prob, transmit immediately.
        - With probability (1-p), wait a random backoff then transmit.
        """
        try:
            if random.random() > self.aloha_prob:
                backoff = random.uniform(self.aloha_backoff_min, self.aloha_backoff_max)
                print(f"[Node {self.node_id}] ALOHA backoff {backoff:.2f}s")
                time.sleep(backoff)

            self.transmit_packet(packet)

        except Exception as e:
            print(f"[Node {self.node_id}] Error in send_with_aloha: {e}")

    def transmit_packet(self, packet):
        """Send packet to physical layer as a PDU"""
        try:
            vec = pmt.init_u8vector(len(packet), list(packet))
            pdu = pmt.cons(pmt.PMT_NIL, vec)
            self.message_port_pub(self.port_pdu_out, pdu)

        except Exception as e:
            print(f"[Node {self.node_id}] Error transmitting packet: {e}")

    # -------------------------------------------------------------------------
    # Go-Back-N TX thread
    # -------------------------------------------------------------------------
    def process_acks(self):
        """Process all pending ACKs and slide the GBN window."""
        try:
            while True:
                ack = self.ack_queue.get_nowait()
                ack_seq = ack['seq']
                # In this simple implementation we don't distinguish by src.
                if not self.tx_window:
                    continue

                if ack_seq not in self.tx_window:
                    # Could be a cumulative ACK for multiple packets.
                    # We remove from the left until we pass ack_seq if it appears.
                    keys = list(self.tx_window.keys())
                    if ack_seq in keys:
                        idx = keys.index(ack_seq)
                        to_remove = keys[:idx + 1]
                    else:
                        # If ack_seq not present, we assume it's older than current base (duplicate) and ignore.
                        continue
                else:
                    # ack_seq is present; treat as cumulative ACK up to this seq.
                    keys = list(self.tx_window.keys())
                    idx = keys.index(ack_seq)
                    to_remove = keys[:idx + 1]

                # Remove all ACKed packets from window (cumulative ACK)
                for s in to_remove:
                    entry = self.tx_window.pop(s, None)
                    if entry is not None and not entry.get('feedback_sent', False):
                        self.send_feedback(True)
                        entry['feedback_sent'] = True

                self.stats['acks_received'] += 1

                # Reset timer/retries based on new window state
                if self.tx_window:
                    self.window_timer_start = time.time()
                    self.window_retries = 0
                else:
                    self.window_timer_start = None
                    self.window_retries = 0

        except queue.Empty:
            # No more ACKs for now
            pass
        except Exception as e:
            print(f"[Node {self.node_id}] Error processing ACKs: {e}")

    def fill_window_from_queue(self):
        """Pull new messages from tx_queue into the Go-Back-N window if there's space."""
        try:
            while len(self.tx_window) < self.window_size:
                try:
                    msg = self.tx_queue.get_nowait()
                except queue.Empty:
                    break

                dst = msg['dst']
                data = msg.get('data', b'')
                pkt_type = msg.get('type', self.PKT_DATA)

                # Assign sequence number
                seq = self.seq_num_tx
                self.seq_num_tx = (self.seq_num_tx + 1) % 256

                packet = self.create_packet(dst, seq, pkt_type, data)

                # For broadcast we typically don't do ARQ; transmit once and don't put in window
                if dst == 0xFF or pkt_type != self.PKT_DATA:
                    print(f"[Node {self.node_id}] TX (no ARQ): seq={seq} dst={dst}")
                    self.send_with_aloha(packet)
                    self.stats['packets_sent'] += 1
                    continue

                # Reliable (GBN-managed) packet
                self.tx_window[seq] = {
                    'packet': packet,
                    'feedback_sent': False,
                }

                print(f"[Node {self.node_id}] TX: Sending DATA seq={seq} dst={dst} (window size={len(self.tx_window)})")
                self.send_with_aloha(packet)
                self.stats['packets_sent'] += 1

                # If this is the first packet in window, start timer
                if len(self.tx_window) == 1:
                    self.window_timer_start = time.time()
                    self.window_retries = 0

        except Exception as e:
            print(f"[Node {self.node_id}] Error filling window: {e}")

    def check_window_timeout(self):
        """Check for Go-Back-N timeout on the base of the window and retransmit if needed."""
        if not self.tx_window:
            return

        if self.window_timer_start is None:
            return

        now = time.time()
        if now - self.window_timer_start < self.timeout:
            return

        # Timeout occurred for base of window
        self.stats['window_timeouts'] += 1
        self.window_retries += 1
        base_seq = next(iter(self.tx_window.keys()))
        print(f"[Node {self.node_id}] GBN timeout at seq={base_seq}, retry {self.window_retries}/{self.max_retries}")

        if self.window_retries > self.max_retries:
            print(f"[Node {self.node_id}] GBN: Max retries exceeded, dropping window")
            # Mark all outstanding packets as failed
            for _seq, entry in list(self.tx_window.items()):
                if not entry.get('feedback_sent', False):
                    self.send_feedback(False)
                    entry['feedback_sent'] = True
            self.tx_window.clear()
            self.window_timer_start = None
            self.window_retries = 0
            return

        # Go-Back-N: retransmit all packets currently in the window
        for seq, entry in self.tx_window.items():
            print(f"[Node {self.node_id}] GBN retransmit seq={seq}")
            self.send_with_aloha(entry['packet'])
            self.stats['retransmissions'] += 1

        # Restart timer for the base
        self.window_timer_start = time.time()

    def tx_handler(self):
        """Thread for handling Go-Back-N transmission + ALOHA medium access."""
        while self.running:
            try:
                # 1) Process all ACKs
                self.process_acks()

                # 2) Check for timeout on window base
                self.check_window_timeout()

                # 3) Fill window with new packets from tx_queue if space
                self.fill_window_from_queue()

                # Small sleep to avoid busy-wait
                time.sleep(0.01)

            except Exception as e:
                print(f"[Node {self.node_id}] TX handler error: {e}")

    # -------------------------------------------------------------------------
    # RX thread (packetization + GBN receiver side)
    # -------------------------------------------------------------------------
    def rx_handler(self):
        """Thread for handling packet reception and GBN RX logic."""
        while self.running:
            try:
                try:
                    rx_data = self.rx_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Append to RX buffer
                self.rx_buffer += rx_data

                # Extract packets from buffer
                while len(self.rx_buffer) > 0:
                    pkt = self.parse_packet(self.rx_buffer)

                    if pkt is None:
                        # No valid packet at current alignment; drop one byte and re-try
                        if len(self.rx_buffer) > 1:
                            self.rx_buffer = self.rx_buffer[1:]
                        else:
                            self.rx_buffer = bytes()
                        continue

                    # Remove processed bytes
                    self.rx_buffer = self.rx_buffer[pkt['consumed']:]

                    # Addressing: packet must be for us or broadcast
                    if pkt['dst'] != self.node_id and pkt['dst'] != 0xFF:
                        print(f"[Node {self.node_id}] RX: Packet not for us (dst={pkt['dst']})")
                        continue

                    if pkt['type'] == self.PKT_DATA:
                        self.handle_data_packet(pkt)
                    elif pkt['type'] == self.PKT_ACK:
                        self.handle_ack_packet(pkt)

            except Exception as e:
                print(f"[Node {self.node_id}] RX handler error: {e}")

    def handle_data_packet(self, pkt):
        """Handle incoming DATA packet with GBN receiver logic."""
        src = pkt['src']
        seq = pkt['seq']
        payload = pkt['payload']

        self.stats['packets_received'] += 1
        expected = self.expected_seq_rx.get(src, 0)

        if seq == expected:
            # In-order packet: accept and advance
            print(f"[Node {self.node_id}] RX: In-order DATA from {src}, seq={seq} (expected={expected})")
            self.expected_seq_rx[src] = (expected + 1) % 256
            ack_seq = seq
            is_new = True
        else:
            # Out-of-order or duplicate
            print(f"[Node {self.node_id}] RX: Out-of-order/dup DATA from {src}, seq={seq}, expected={expected}")
            # Last correctly received in-order seq is expected-1 (mod 256)
            if expected == 0:
                ack_seq = 255
            else:
                ack_seq = (expected - 1) & 0xFF
            is_new = False

        # Send ACK for last in-order seq (GBN cumulative ACK)
        ack_packet = self.create_packet(src, ack_seq, self.PKT_ACK)
        print(f"[Node {self.node_id}] RX: Sending ACK seq={ack_seq} to {src}")
        self.send_with_aloha(ack_packet)
        self.stats['acks_sent'] += 1

        # Deliver only new, in-order packets to the application
        if is_new:
            self.forward_to_app(src, payload)

    def handle_ack_packet(self, pkt):
        """Handle incoming ACK packet (push to ack_queue for TX thread)."""
        src = pkt['src']
        seq = pkt['seq']
        print(f"[Node {self.node_id}] RX: ACK from node {src}, seq={seq}")
        # Push seq to ack queue; TX thread handles window sliding
        self.ack_queue.put({'src': src, 'seq': seq})

    # -------------------------------------------------------------------------
    # Upper-layer delivery & feedback
    # -------------------------------------------------------------------------
    def forward_to_app(self, src_id, data):
        """Forward received data to application/GUI."""
        try:
            message = data.decode('utf-8', errors='ignore')
            output = f"[From Node {src_id}]: {message}"

            # Simple string out
            msg = pmt.intern(output)
            self.message_port_pub(self.port_msg_out, msg)

            # (Optional) could also send a dict PDU here if needed
            print(f"[Node {self.node_id}] Message delivered: {output}")

        except Exception as e:
            print(f"[Node {self.node_id}] Error forwarding to app: {e}")

    def send_feedback(self, success):
        """Send boolean-like feedback (TRUE/FALSE) to feedback port."""
        try:
            text = "TRUE" if success else "FALSE"
            msg = pmt.intern(text)
            self.message_port_pub(self.port_feedback, msg)
        except Exception as e:
            print(f"[Node {self.node_id}] Error sending feedback: {e}")

    # -------------------------------------------------------------------------
    # GNU Radio boilerplate
    # -------------------------------------------------------------------------
    def work(self, input_items, output_items):
        """Main work function (not used for message-passing block)."""
        return 0

    def stop(self):
        """Clean shutdown"""
        print(f"\n[Node {self.node_id}] Statistics:")
        print(f"  Packets sent:      {self.stats['packets_sent']}")
        print(f"  Packets received:  {self.stats['packets_received']}")
        print(f"  ACKs sent:         {self.stats['acks_sent']}")
        print(f"  ACKs received:     {self.stats['acks_received']}")
        print(f"  Retransmissions:   {self.stats['retransmissions']}")
        print(f"  CRC errors:        {self.stats['crc_errors']}")
        print(f"  Window timeouts:   {self.stats['window_timeouts']}")

        self.running = False
        if self.tx_thread.is_alive():
            self.tx_thread.join()
        if self.rx_thread.is_alive():
            self.rx_thread.join()
        return True
