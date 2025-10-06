"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import os.path
import pmt







class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self, confirm_file = 'None', request_number_file = 'None'):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Embedded Python Block',   # will show up in GRC
            in_sig=None,
            out_sig=[np.uint8]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.confirm_file = confirm_file
        self.request_number_file = request_number_file
        self.state = 0
        self.user_address = "11"
        self.request_num = None
        self.indx = 0

    def headify(self, bits):
        return self.user_address + bits
    
    def CRC_adder(self, bits):
        poly = 0x104C11DB7
        data = int(bits, 2)
        data <<= 32
        poly_length = poly.bit_length()
        while data.bit_length() >= poly_length:
            data ^= poly << (data.bit_length() - poly_length)
        crc_bits = format(data, "032b")
        return bits + crc_bits




    def work(self, input_items, output_items):
        """example: multiply with constant"""
        
        if (self.state == 0):
            if (os.path.exists(self.confirm_file)):
                with open(self.confirm_file, "r") as confirm_file:
                    c = confirm_file.read().strip()
                    if (c == "True"):
                        if (os.path.exists(self.request_number_file)):
                            with open(self.request_number_file , "r") as req_num_file:
                                self.request_num = int(req_num_file.read().strip())
                                self.state = 1
                        else:
                            self.state = 7
                            print("the request number file did not exist")
                    else:
                        self.state = 0
            else:
                self.state = 7
                print("the confirm file did not exist")
            return (0)
        
        if (self.state == 1): 
            req_num_bits = format(self.request_num, "06b")
            headed_msg = self.headify(req_num_bits)
            final_msg = self.CRC_adder(headed_msg)

            msg_bytes = np.packbits(np.frombuffer(final_msg.encode("ascii"), dtype=np.uint8) - 48) # [43 65 34 34 23 23 54 23]
            msg_len = len(msg_bytes)

            key0 = pmt.intern("packet_len")
            val0 = pmt.from_long(msg_len)
            self.add_item_tag(0,
                              self.indx,
                              key0,
                              val0,
                              )
            self.indx += msg_len


            i=0
            while (i < msg_len):
                output_items[0][i] = msg_bytes[i]
                i += 1
            
            self.state = 0

            if (os.path.exists(self.confirm_file)):
                with open(self.confirm_file, "w") as con_file:
                    con_file.write("False")


            return (msg_len)




        
        
        # output_items[0][:] = input_items[0] * self.example_param
        # return len(output_items[0])
