#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr
import pmt

class bitstream_to_pdu(gr.sync_block):
    """
    Converts a framed bitstream back to PDU messages.
    Searches for sync word and reconstructs PDUs based on length field.
    Frame format: [SYNC_WORD (4 bytes)] [LENGTH (2 bytes)] [DATA (N bytes)]
    """
    def __init__(self, sync_word=0x1ACFFC1D, threshold=0):
        gr.sync_block.__init__(
            self,
            name="Bitstream to PDU",
            in_sig=[np.uint8],
            out_sig=None
        )
        
        self.message_port_register_out(pmt.intern('pdu_out'))
        
        self.sync_word = sync_word
        self.threshold = threshold  # Number of bit errors allowed in sync
        
        # Convert sync word to bit pattern
        sync_bytes = np.array([
            (sync_word >> 24) & 0xFF,
            (sync_word >> 16) & 0xFF,
            (sync_word >> 8) & 0xFF,
            sync_word & 0xFF
        ], dtype=np.uint8)
        self.sync_bits = np.unpackbits(sync_bytes)
        
        self.bit_buffer = []
        self.state = 'SEARCH'  # States: SEARCH, READ_LENGTH, READ_DATA
        self.pdu_length = 0
        self.bits_needed = 0
        
    def correlate_sync(self, bits):
        """Check if bits match sync word (with threshold)"""
        if len(bits) < len(self.sync_bits):
            return False
        
        errors = np.sum(bits[:len(self.sync_bits)] != self.sync_bits)
        return errors <= self.threshold
    
    def work(self, input_items, output_items):
        """Process input bitstream and reconstruct PDUs"""
        in0 = input_items[0]
        n_input = len(in0)
        
        # Add incoming bits to buffer
        self.bit_buffer.extend(in0[:n_input].tolist())
        
        # Process buffer based on current state
        while True:
            if self.state == 'SEARCH':
                # Search for sync word
                if len(self.bit_buffer) >= len(self.sync_bits):
                    if self.correlate_sync(np.array(self.bit_buffer[:len(self.sync_bits)])):
                        # Found sync word, remove it from buffer
                        self.bit_buffer = self.bit_buffer[len(self.sync_bits):]
                        self.state = 'READ_LENGTH'
                    else:
                        # Shift by one bit and continue searching
                        self.bit_buffer.pop(0)
                else:
                    break  # Not enough bits yet
                    
            elif self.state == 'READ_LENGTH':
                # Need 16 bits (2 bytes) for length
                if len(self.bit_buffer) >= 16:
                    # Extract length bits and convert to bytes
                    length_bits = np.array(self.bit_buffer[:16], dtype=np.uint8)
                    length_bytes = np.packbits(length_bits)
                    self.pdu_length = (int(length_bytes[0]) << 8) | int(length_bytes[1])
                    
                    # Remove length bits from buffer
                    self.bit_buffer = self.bit_buffer[16:]
                    
                    # Calculate bits needed for data
                    self.bits_needed = self.pdu_length * 8
                    self.state = 'READ_DATA'
                else:
                    break  # Not enough bits yet
                    
            elif self.state == 'READ_DATA':
                # Check if we have all data bits
                if len(self.bit_buffer) >= self.bits_needed:
                    # Extract data bits
                    data_bits = np.array(self.bit_buffer[:self.bits_needed], dtype=np.uint8)
                    self.bit_buffer = self.bit_buffer[self.bits_needed:]
                    
                    # Pack bits back into bytes
                    data_bytes = np.packbits(data_bits)
                    
                    # Create and send PDU (with empty metadata)
                    pdu_vector = pmt.init_u8vector(len(data_bytes), data_bytes.tolist())
                    pdu = pmt.cons(pmt.make_dict(), pdu_vector)
                    self.message_port_pub(pmt.intern('pdu_out'), pdu)
                    
                    # Go back to searching for next frame
                    self.state = 'SEARCH'
                else:
                    break  # Not enough bits yet
        
        return n_input
