import numpy as np
from gnuradio import gr
import pmt


##################################################
# BLOCK 1: PDU to Bitstream (Variable Length)
##################################################
class pdu_to_bitstream(gr.sync_block):
    """
    Converts PDU bytes to bits with length header.
    
    Format:
    - Length (16 bits): Number of payload bytes (0-65535)
    - Payload (N bytes): Actual PDU data
    
    Input: PDU messages (variable length)
    Output: Byte stream (unpacked bits, 1 bit per byte)
    """
    
    def __init__(self, length_bits=16):
        gr.sync_block.__init__(
            self,
            name="PDU to Bitstream",
            in_sig=None,
            out_sig=[np.uint8]
        )
        
        self.length_bits = length_bits  # Bits used for length field
        self.max_length = (1 << length_bits) - 1
        
        # Message port for PDU input
        self.message_port_register_in(pmt.intern('pdus'))
        self.set_msg_handler(pmt.intern('pdus'), self.handle_pdu)
        
        # Buffer to hold bits waiting to be output
        self.bit_buffer = []
        
    def handle_pdu(self, msg):
        """Handle incoming PDU and convert to bits with length header"""
        try:
            # Extract PDU data
            meta = pmt.car(msg)
            data = pmt.cdr(msg)
            
            if pmt.is_u8vector(data):
                payload = bytes(pmt.u8vector_elements(data))
            else:
                print("Warning: PDU data is not u8vector")
                return
            
            payload_len = len(payload)
            
            # Check length limits
            if payload_len > self.max_length:
                print(f"Error: PDU length {payload_len} exceeds maximum {self.max_length}")
                return
            
            # Convert length to bits (MSB first)
            for i in range(self.length_bits - 1, -1, -1):
                bit = (payload_len >> i) & 1
                self.bit_buffer.append(bit)
            
            # Convert payload bytes to bits (MSB first)
            for byte in payload:
                for i in range(7, -1, -1):
                    bit = (byte >> i) & 1
                    self.bit_buffer.append(bit)
            
            total_bits = self.length_bits + (payload_len * 8)
            print(f"[PDU→Bitstream] Added {payload_len} bytes ({total_bits} bits total with length header)")
            
        except Exception as e:
            print(f"Error handling PDU: {e}")
            import traceback
            traceback.print_exc()
    
    def work(self, input_items, output_items):
        """Output bits from buffer"""
        output = output_items[0]
        n_output = len(output)
        
        if not self.bit_buffer:
            # No data, output zeros
            output[:] = 0
            return n_output
        
        # Output available bits
        n_bits = min(n_output, len(self.bit_buffer))
        output[:n_bits] = self.bit_buffer[:n_bits]
        
        # Remove output bits from buffer
        self.bit_buffer = self.bit_buffer[n_bits:]
        
        # Pad rest with zeros if needed
        if n_bits < n_output:
            output[n_bits:] = 0
        
        return n_output
