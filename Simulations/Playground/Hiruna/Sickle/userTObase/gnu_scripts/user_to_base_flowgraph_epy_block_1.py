"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import os.path

folder = "D:/Academics/Semester 3/CDP/Repo/Simulations/Playground/Hiruna/Sickle"

state = 0
addr = "11"

request_file = os.path.join(folder, "userTObase", "rec_side_stuff", "misc", "req_num.txt")
confirm_file = os.path.join(folder, "userTObase", "rec_side_stuff", "misc", "confirm.txt")



def crc_generator(bits):
    poly = 0x104C11DB7

    data = int(bits, 2)

    data <<= 32

    poly_length = poly.bit_length()

    while data.bit_length() >= poly_length:
        data ^= poly << (data.bit_length() - poly_length)
    
    crc_bits = format(data, "032b")

    return crc_bits



class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self):  # only default arguments here
        
        gr.sync_block.__init__(
            self,
            name='ack receiver block',   # will show up in GRC
            in_sig=[np.uint8],
            out_sig=None
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.buffer = bytearray()



    def work(self, input_items, output_items):
        
        in_bytes = input_items[0]

        self.buffer.extend(in_bytes)

        print("bytes: ", in_bytes)


        while len(self.buffer) >= 5:
            msg = self.buffer[:5]
            self.buffer = self.buffer[5:]

            bit_str = ''.join(f"{b:08b}" for b in msg)

            doTheThing(bit_str)

            bit_str = ''

        return len(in_bytes)






def doTheThing(bit_str):
    
    header_string = bit_str[:8]

    if int(crc_generator(bit_str)) != 0:
        print('CRC failed')
        return
    else:
        print('CRC successful')

        rx_addr = header_string[:2]
        rx_seq = header_string[2:8]

        if rx_addr != addr:
            print("incorrect address")
            return 
        
        request_number = rx_seq

        with open(request_file, "w") as req_file:
            req_file.write(str(request_number))
        
        with open(confirm_file, "w") as con_file:
            con_file.write("True")

        







