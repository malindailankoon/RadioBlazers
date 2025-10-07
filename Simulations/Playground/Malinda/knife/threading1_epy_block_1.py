#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr
import pmt

class pdu_to_bitstream(gr.sync_block):
    """
    Converts PDU messages to a framed bitstream.
    Frame format: [SYNC_WORD (4 bytes)] [LENGTH (2 bytes)] [DATA (N bytes)]
    Each byte is unpacked into 8 bits (MSB first).
    """
    def __init__(self, sync_word=0x1ACFFC1D):
        gr.sync_block.__init__(
            self,
            name="PDU to Bitstream",
            in_sig=None,
            out_sig=[np.uint8]
        )
        
        self.message_port_register_in(pmt.intern('pdu_in'))
        self.set_msg_handler(pmt.intern('pdu_in'), self.handle_pdu)
        
        self.sync_word = sync_word
        self.bit_buffer = []
        
    def handle_pdu(self, pdu):
        """Handle incoming PDU messages"""
        # Extract data from PDU (ignore metadata for now)
        data = pmt.cdr(pdu)
        
        # Convert PMT vector to numpy array
        if pmt.is_u8vector(data):
            data_bytes = np.array(pmt.u8vector_elements(data), dtype=np.uint8)
        else:
            return
        
        # Build frame: [SYNC][LENGTH][DATA]
        frame = []
        
        # Add sync word (4 bytes, big-endian)
        sync_bytes = np.array([
            (self.sync_word >> 24) & 0xFF,
            (self.sync_word >> 16) & 0xFF,
            (self.sync_word >> 8) & 0xFF,
            self.sync_word & 0xFF
        ], dtype=np.uint8)
        frame.extend(sync_bytes)
        
        # Add length (2 bytes, big-endian)
        length = len(data_bytes)
        length_bytes = np.array([
            (length >> 8) & 0xFF,
            length & 0xFF
        ], dtype=np.uint8)
        frame.extend(length_bytes)
        
        # Add data
        frame.extend(data_bytes)
        
        # Convert frame to numpy array and unpack to bits
        frame_array = np.array(frame, dtype=np.uint8)
        bits = np.unpackbits(frame_array)
        
        # Add bits to buffer
        self.bit_buffer.extend(bits.tolist())
    
    def work(self, input_items, output_items):
        """Output buffered bits"""
        out = output_items[0]
        
        # Determine how many bits to output
        n_output = min(len(self.bit_buffer), len(out))
        
        if n_output > 0:
            # Copy bits to output
            out[:n_output] = self.bit_buffer[:n_output]
            # Remove outputted bits from buffer
            self.bit_buffer = self.bit_buffer[n_output:]
            
        return n_output