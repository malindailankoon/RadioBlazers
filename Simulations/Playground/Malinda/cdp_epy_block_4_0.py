#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pmt
import zlib
from gnuradio import gr

class crc_forwarder(gr.basic_block):
    """
    CRC32 Checker + Dedup + Forwarder (Message Reassembler)
    - Input : [sender_addr | seq_id | payload | crc32]
    - Output: [sender_addr | full_message] only when end marker received
    - End marker: valid packet with empty payload
    - Handles multiple senders dynamically
    - ACK prepends transmitter's address and appends CRC32
    """

    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="CRC32 Dedup + Forwarder",
            in_sig=[],
            out_sig=[]
        )

        self.received_ids = set()  # track processed (addr, seq_id)
        self.buffers = {}          # per-sender message buffer

        # Ports
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))      # forward reassembled message
        self.message_port_register_out(pmt.intern("ack_out"))  # ACKs

        self.set_msg_handler(pmt.intern("in"), self._handle_msg)

        print("[CRC32] Receiver initialized")

    def _handle_msg(self, msg):
        if not pmt.is_pair(msg):
            return
        vec = pmt.cdr(msg)
        if not pmt.is_u8vector(vec):
            return

        data = bytearray(pmt.u8vector_elements(vec))
        if len(data) < 6:  # minimum frame length [addr | seq | (opt payload) | crc32]
            print("[CRC32] Frame too short")
            return

        sender_addr = data[0]  # transmitter address
        pkt_id = data[1]
        payload = data[2:-4]
        recv_crc = int.from_bytes(data[-4:], "big")
        calc_crc = zlib.crc32(bytes([sender_addr, pkt_id]) + payload) & 0xFFFFFFFF

        if calc_crc != recv_crc:
            print(f"[CRC32] FAIL (Addr 0x{sender_addr:02X}, ID {pkt_id})")
            return

        # ✅ CRC OK
        print(f"[CRC32] OK (Addr 0x{sender_addr:02X}, ID {pkt_id})")

        # --- Construct ACK like address_add block, then append CRC32 ---
        ack_data = bytearray([sender_addr, 0xAA, pkt_id])
        ack_crc = zlib.crc32(ack_data) & 0xFFFFFFFF
        ack_data += ack_crc.to_bytes(4, 'big')

        ack_vec = pmt.init_u8vector(len(ack_data), list(ack_data))
        ack_pdu = pmt.cons(pmt.PMT_NIL, ack_vec)
        self.message_port_pub(pmt.intern("ack_out"), ack_pdu)
        print(f"[ACK] Sent to transmitter Addr 0x{sender_addr:02X}, ID {pkt_id}, CRC32 0x{ack_crc:08X}")

        # Deduplication
        if (sender_addr, pkt_id) in self.received_ids:
            print(f"[Forward] Addr 0x{sender_addr:02X}, ID {pkt_id} duplicate, ignored")
            return
        self.received_ids.add((sender_addr, pkt_id))

        # Empty payload = END marker
        if len(payload) == 0:
            if sender_addr in self.buffers and self.buffers[sender_addr]:
                full_payload = b''.join(self.buffers[sender_addr])
                forward_bytes = bytes([sender_addr]) + full_payload
                out_vec = pmt.init_u8vector(len(forward_bytes), list(forward_bytes))
                out_msg = pmt.cons(pmt.PMT_NIL, out_vec)
                self.message_port_pub(pmt.intern("out"), out_msg)
                print(f"[Forward] Addr 0x{sender_addr:02X}, END marker → {len(full_payload)} bytes reassembled and forwarded")
            else:
                print(f"[Forward] Addr 0x{sender_addr:02X}, END marker but no buffered data")
            self.buffers[sender_addr] = []
        else:
            if sender_addr not in self.buffers:
                self.buffers[sender_addr] = []
            self.buffers[sender_addr].append(payload)
            total_len = sum(len(p) for p in self.buffers[sender_addr])
            print(f"[Buffer] Addr 0x{sender_addr:02X}, ID {pkt_id} → {len(payload)} bytes buffered (total {total_len})")

