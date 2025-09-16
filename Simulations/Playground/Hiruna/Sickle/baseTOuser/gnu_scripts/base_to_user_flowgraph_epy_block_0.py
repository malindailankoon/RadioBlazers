# Embedded Python Block
# Input: byte stream (numpy uint8)
# Output: just prints full 13-byte messages when available

import numpy as np
from gnuradio import gr
import os.path
import sys
import struct
import subprocess


folder = "D:/Academics/Semester 3/CDP/Repo/Simulations/Playground/Hiruna/Sickle"

state = 0
addr = "11"
# base_dir = os.path.dirname(__file__)
path_to_output_tmp = os.path.join(folder, "baseTOuser", "rec_side_stuff.", "misc", "output.tmp")
request_file = os.path.join(folder, "baseTOuser", "misc", "req_num.txt") # '../misc/req_num.txt' 
confirm_file = os.path.join(folder, "baseTOuser", "misc", "confirm.txt") # '../misc/confirm.txt' 
output_file = os.path.join(folder, "baseTOuser", "misc", "final.txt") # '../misc/final.txt'
# message_file = "message.txt"
req = 0
packet = ''
pkt_size = 64
end_file_delimiter = "1010101010101010101010101010101010101010101010101010101010101010"
headed_pkt_list = []

## CODE FOR TESTING!
testing_req_file = os.path.join(folder, "userTObase", "rec_side_stuff", "misc", "request.txt")
testing_con_file = os.path.join(folder, "userTObase", "rec_side_stuff", "misc", "confirm.txt")
##-----------------


def deheadify(headed_pkt_list):
    payload_bit_string = ""

    for headed_pkt in headed_pkt_list:
        addr = headed_pkt[0:2]
        seq_no = headed_pkt[2:8]
        payload = headed_pkt[8:72]
        crc = headed_pkt[72:104]

        payload_bit_string += payload
    
    size_bits = payload_bit_string[-12:]

    size = int(size_bits, 2)
    msg_bitstring = payload_bit_string[:size]

    byte_list = [int(msg_bitstring[i:i+8], 2) for i in range(0, len(msg_bitstring), 8)]
    data_bytes = bytes(byte_list)
    text = data_bytes.decode("utf-8")

    return text


def crc_generator(bits): # bits should be a bit string |||  the output will also be 32bit string
    poly = 0x104C11DB7

    data = int(bits,2)

    data <<= 32

    poly_length = poly.bit_length()

    while data.bit_length() >= poly_length:
        data ^= poly << (data.bit_length() - poly_length)

    crc_bits = format(data, "032b")
    # print(len(bits), len(crc_bits))
    return crc_bits


class blk(gr.sync_block):
    """
    Collects bytes and prints a message every 13 bytes.
    """
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="Print 13-byte message",
            in_sig=[np.uint8],
            out_sig=None  # No output stream
        )
        self.buffer = bytearray()  # store incoming bytes

    def work(self, input_items, output_items):
        in_bytes = input_items[0]

        # Append incoming bytes to buffer
        self.buffer.extend(in_bytes)

        print("bytes : ", in_bytes)

        # Check if we have a full 13-byte message
        while len(self.buffer) >= 13:
            msg = self.buffer[:13]           # take first 13 bytes
            self.buffer = self.buffer[13:]   # remove them from buffer

            # Convert to hex string or bit string for printing
            hex_str = ' '.join(f"{b:02X}" for b in msg)
            bit_str = ''.join(f"{b:08b}" for b in msg)

            print(f"13-byte message (hex): {hex_str}")
            #print(f"13-byte message (bits): {bit_str}\n")

            doTheThing(bit_str)

            bit_str = ''


        return len(in_bytes)


print("oshan program started!")


def doTheThing(bit_str):
    global req  # <--- Add this
    global headed_pkt_list  # needed if you want to append packets
    rx_crc_string = bit_str[-32:]
    header_string = bit_str[:8]
    payload_string = bit_str[8:-32]
    
    #print("input packet with header", bit_str)

    if int(crc_generator(bit_str)) != 0:
        print('CRC Failed')
        state2()
        return
    else:
        print("CRC successful")

        rx_addr = header_string[:2]   # first 2 bits
        rx_seq = header_string[2:8]

        if rx_addr != addr: 
            print("Incorrect Address")
            return

        if req == int(rx_seq, 2):
            req += 1  # works now because req is global
            with open(request_file, "w") as req_file:
                req_file.write(str(req))
            with open(testing_req_file, "w") as req_file:
                req_file.write(str(req))
            
            state2()
            
            print("received payload packet => ", payload_string)
            if payload_string == end_file_delimiter:
                text = deheadify(headed_pkt_list)
                print(text)
                with open(output_file, "w") as o_file:
                    o_file.write(text)
                
                
            else:
                headed_pkt_list.append(bit_str)
        else:
            print("incorrect seq number")
            state2()
        print("req ", req)


def state2():
    global req  # <--- Add this
    print("oshan: state 2 started")
    print("Sending ACK for ", req)
    with open(testing_con_file, "w") as conf:
        conf.write("True")

        



