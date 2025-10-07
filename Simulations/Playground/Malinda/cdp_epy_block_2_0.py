#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import pmt
from gnuradio import gr
import time

class pdu_text_gui(gr.basic_block):
    """
    Custom block: QT GUI Message Entry -> PDU sender with Go-Back-N ARQ.
    - Splits text into packets (2 bytes: [address, seq_id] + payload)
    - Sends packets in a sliding window
    - Waits for ACKs [0xAA, seq_id]
    - On timeout, retransmits all unACKed packets in window
    - After full message, sends END packet [address, seq_id] (no payload)
    - Sends feedback to GUI when END ACK is received
    - Sends feedback if retry limit is exceeded
    """

    def __init__(self, wait_time=2.0, pkt_size=32, address=0x01, retry_limit=100, window_size=4):
        gr.basic_block.__init__(
            self,
            name="GUI Text to PDU with Go-Back-N ARQ",
            in_sig=[],
            out_sig=[]
        )

        # Parameters
        self._timeout = float(wait_time)
        self._pkt_size = int(pkt_size)
        self._address = int(address) & 0xFF
        self._retry_limit = int(retry_limit)
        self._window_size = int(window_size)

        # Sequence ID
        self._seq_id = 1  # 0x01..0xFF, avoid 0x00

        # Message ports
        self.message_port_register_out(pmt.intern("out"))
        self.message_port_register_out(pmt.intern("feedback"))  # feedback port for GUI

        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_in(pmt.intern("ack_in"))

        self.set_msg_handler(pmt.intern("in"), self._process_text)
        self.set_msg_handler(pmt.intern("ack_in"), self._process_ack)

        # Thread + synchronization
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Buffers
        self._text_data = b""
        self._packets = []
        self._base = 0          # first unACKed packet index
        self._next_to_send = 0  # next packet index to send
        self._attempts = 0
        self._end_seq_id = 0     # store END packet seq_id for feedback

    # ---------------------------
    # Message handler from GUI
    # ---------------------------
    def _process_text(self, msg):
        try:
            if pmt.is_symbol(msg):
                text_str = pmt.symbol_to_string(msg)
            elif pmt.is_string(msg):
                text_str = pmt.string_to_string(msg)
            else:
                print("[pdu_text_gui] Invalid PMT message type")
                return

            self._text_data = text_str.encode("utf-8")

            # Start sending in a separate thread
            if self._thread is None or not self._thread.is_alive():
                self._stop_event.clear()
                self._thread = threading.Thread(target=self._run)
                self._thread.daemon = True
                self._thread.start()

        except Exception as e:
            print(f"[pdu_text_gui] Error processing text: {e}")

    # ---------------------------
    # Sending loop (Go-Back-N)
    # ---------------------------
    def _run(self):
        raw = self._text_data
        step = self._pkt_size - 2
        blocks = [raw[i:i+step] for i in range(0, len(raw), step)]

        # Build packets with headers
        self._packets = []
        for block in blocks:
            packet = bytes([self._address, self._seq_id]) + block
            self._packets.append((self._seq_id, packet))
            self._seq_id = (self._seq_id + 1) & 0xFF
            if self._seq_id == 0:
                self._seq_id = 1

        # Add END packet (address + seq_id, no payload)
        end_packet = bytes([self._address, self._seq_id])
        self._packets.append((self._seq_id, end_packet))
        self._end_seq_id = self._seq_id  # store END packet seq_id for feedback
        print(f"[pdu_text_gui] End packet prepared (id=0x{self._seq_id:02X})")
        self._seq_id = (self._seq_id + 1) & 0xFF
        if self._seq_id == 0:
            self._seq_id = 1

        self._base = 0
        self._next_to_send = 0
        self._attempts = 0

        while self._base < len(self._packets) and not self._stop_event.is_set():
            with self._lock:
                # Send up to window_size packets
                while self._next_to_send < self._base + self._window_size and self._next_to_send < len(self._packets):
                    seq_id, packet = self._packets[self._next_to_send]
                    vec = pmt.init_u8vector(len(packet), list(packet))
                    pdu = pmt.cons(pmt.PMT_NIL, vec)
                    self.message_port_pub(pmt.intern("out"), pdu)
                    if len(packet) > 2:
                        print(f"[pdu_text_gui] Packet id=0x{seq_id:02X} sent")
                    else:
                        print(f"[pdu_text_gui] END packet id=0x{seq_id:02X} sent")
                    self._next_to_send += 1

            # Wait for ACK
            time.sleep(self._timeout)

            with self._lock:
                if self._base < self._next_to_send:  # still unACKed packets
                    self._attempts += 1
                    if self._attempts >= self._retry_limit:
                        print("[pdu_text_gui] Failed: retry limit exceeded")
                        # Send feedback to GUI about retry limit exceeded
                        self.message_port_pub(pmt.intern("feedback"), pmt.intern("RETRY_LIMIT_EXCEEDED"))
                        self._stop_event.set()
                        break
                    print("[pdu_text_gui] Timeout: retransmitting window")
                    # retransmit all unACKed packets
                    for i in range(self._base, self._next_to_send):
                        seq_id, packet = self._packets[i]
                        vec = pmt.init_u8vector(len(packet), list(packet))
                        pdu = pmt.cons(pmt.PMT_NIL, vec)
                        self.message_port_pub(pmt.intern("out"), pdu)
                        if len(packet) > 2:
                            print(f"[pdu_text_gui] Retransmit id=0x{seq_id:02X}")
                        else:
                            print(f"[pdu_text_gui] Retransmit END id=0x{seq_id:02X}")

    # ---------------------------
    # ACK handler
    # ---------------------------
    def _process_ack(self, msg):
        try:
            payload = pmt.cdr(msg)
            if not pmt.is_u8vector(payload):
                return

            arr = bytearray(pmt.u8vector_elements(payload))
            if len(arr) < 2 or arr[0] != 0xAA:
                return

            ack_id = arr[1]
            with self._lock:
                # slide window if ACK is valid
                for i in range(self._base, self._next_to_send):
                    seq_id, _ = self._packets[i]
                    if seq_id == ack_id:
                        if len(self._packets[i][1]) > 2:
                            print(f"[pdu_text_gui] ACK received for id=0x{ack_id:02X}")
                        else:
                            print(f"[pdu_text_gui] ACK received for END id=0x{ack_id:02X}")
                            # Send feedback to GUI for final ACK
                            self.message_port_pub(pmt.intern("feedback"), pmt.intern("END_ACK_RECEIVED"))
                        self._base = i + 1
                        self._attempts = 0  # reset retries
                        break

        except Exception as e:
            print(f"[pdu_text_gui] Error processing ACK: {e}")

