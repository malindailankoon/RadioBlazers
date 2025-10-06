"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import os.path
import time
import pmt

"""
states: 
    0 - main cheking state: TODO
    1 - this state will again send the current packet, then start the timer change the state back to 0
    2 - this will send the next packet, start the timer and then change the state back to 0 and write "False" to the confirm.txt file
    3 - sending the end_of_file packet then will shift to state 4
    4 - idle state. nothing will happen from this point on
    
    7 - ERROR STATE
"""

class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.elapsed = 0.0
    
    def start(self):
        if self.start_time is None:
            self.start_time = time.perf_counter()
    
    def stop(self):
        if self.start_time is not None:
            self.elapsed += time.perf_counter() - self.start_time
            self.start_time = None
    
    def reset(self):
        self.start_time = None
        self.elapsed = 0.0
    
    def get_time(self):
        if self.start_time is not None:  # running
            return self.elapsed + (time.perf_counter() - self.start_time)
        return self.elapsed

def packify(data_bit_string, pkt_len):
    pkt_list = []
    number_of_packets = int(len(data_bit_string) / pkt_len)
    i = 0
    for _ in range(number_of_packets):
        pkt = data_bit_string[i:i+ pkt_len]
        pkt_list.append(pkt)
        i += 64
    return pkt_list


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


def headify(pkt_list):
    # the header format =>     | addr - 2bits | seq_no - 6bits  | payload - 64bits | crc - 32bits |
    seq_no = 0
    headed_pkt_list = []
    addr = "11" # dummy address
    for pkt in pkt_list:
        headed_pkt = ""
        headed_pkt += addr
        seq_no_bits = format(seq_no, '06b') # convert the sequence number into 6bit bitstring
        headed_pkt += seq_no_bits
        headed_pkt += pkt
        crc_bits = crc_generator(pkt)
        headed_pkt += crc_bits
        headed_pkt_list.append(headed_pkt)
    
    return headed_pkt_list






class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block


    def __init__(self, message_file='None', confirmation_file = 'None', request_number_file = 'None', timeout_period = 5):  # only default arguments here

        gr.sync_block.__init__(
            self,
            name='advanced pickaxe packet sender',   # will show up in GRC
            in_sig=None,
            out_sig=[np.uint8]
        )
        
        self.message_file = message_file # contains the message
        self.confirmation_file = confirmation_file # contains whether an ACK is received or not
        self.request_number_file = request_number_file # contains the request number of the received ACK
        self.state = 0
        self.final_packet_sent = False
        self.seq = 0
        self.msg_size = 0 # this will store the number of bits in the message
        self.pkt_size = 64 # number of bits in the payload
        self.current_pkt = ""
        self.timeout_period = timeout_period
        self.indx = 0
        self.end_file_delimiter = "1010101010101010101010101010101010101010101010101010101010101010"
        self.end_file_sent = False


        # loading the message and making a payload list
        self.payload_list = []
        if (os.path.exists(self.message_file)):
            with open(self.message_file, "rb") as msg_file:
                data = msg_file.read()
                self.msg_size = len(data) * 8

                size_bit_string = format(self.msg_size, "012b")

                number_of_padding = (self.pkt_size -((self.msg_size + 12) % self.pkt_size)) % self.pkt_size

                data_bitstring = ''.join(format(byte, "08b") for byte in data)
                padding_bitstring = '0' * number_of_padding

                final_bitstring = data_bitstring + padding_bitstring + size_bit_string

                pkt_list = packify(final_bitstring)

                self.payload_list = headify(pkt_list)
        else:
            print("the message file does not exist")
            self.state = 4

        self.timer = Stopwatch()
        self.timer.start()





                

    def work(self, input_items, output_items):

        if (self.state == 0):
            if (self.timer > self.timeout_period):
                self.timer.reset()
                self.state = 1
                return (0)
            
            if (os.path.exists(self.confirmation_file)):
                with open(self.confirmation_file, "r") as confirm_file:
                    c = str(confirm_file.read().strip())
                    if (c == "True"):
                        if (os.path.exists(self.request_number_file)):
                            with open(self.request_number_file, "r") as req_file:
                                rn = int(req_file.read().strip())
                                if (rn > self.seq):
                                    self.timer.reset()
                                    self.seq += 1
                                    if (len(self.payload_list) > 0):
                                        self.state = 2
                                        return (0)
                                    else:
                                        if (self.end_file_sent == True):
                                            self.state = 4
                                        else:
                                            self.state = 3
                                        return (0)
                                else:
                                    self.state = 0
                                    return (0)

                        else:
                            print(" the request number file did not exist")
                            self.state = 7
                    
                    else:
                        self.state = 0
                        return (0)
                        
            else:
                print(" the confirm.txt file did not exists")
                self.state = 7
        


        elif (self.state == 1):
            pkt_bytes = np.packbits(np.frombuffer(self.current_pkt.encode("ascii"), dtype=np.uint8) - 48) # [43 65 34 34 23 23 54 23]
            p_len = len(pkt_bytes)

            key0 = pmt.intern("packet_len")
            val0 = pmt.from_long(p_len)
            self.add_item_tag(0,
                              self.indx,
                              key0,
                              val0
                              )
            self.indx += p_len

            i = 0
            while (i < p_len):
                output_items[0][i] = pkt_bytes[i]
                i += 1
            
            # if (os.path.exists(self.confirmation_file)):
            #     with open(self.confirmation_file, "w") as confirm_file:
            #         confirm_file.write("False")

            self.state = 0

            self.timer.start()
            return (p_len)
        



        elif (self.state == 2): # sending the next packet
            self.current_pkt = self.payload_list.pop(0)

            pkt_bytes = np.packbits(np.frombuffer(self.current_pkt.encode("ascii"), dtype=np.uint8) - 48)
            p_len = len(pkt_bytes)

            key0 = pmt.intern("packet_len")
            val0 = pmt.from_long(p_len)
            self.add_item_tag(0,
                              self.indx,
                              key0,
                              val0
                              )
            self.indx += p_len

            i = 0
            while (i < p_len):
                output_items[0][i] = pkt_bytes[i]
                i += 1
            
            if (os.path.exists(self.confirmation_file)):
                with open(self.confirmation_file, "w") as confirm_file:
                    confirm_file.write("False")
            
            self.state = 0

            self.timer.start()
            return(p_len)
        


        elif (self.state == 3):
            # sending the end of file delimeter packet
            
            pkt = self.end_file_delimiter

            seq_bits = format(self.seq, "06b")
            pkt = seq_bits + pkt

            addr = "11"
            pkt = addr + pkt

            crc_bits = crc_generator(pkt)
            pkt = pkt + crc_bits

            pkt_bytes = np.packbits(np.frombuffer(pkt.encode("ascii"), dtype=np.uint8) - 48)
            p_len = len(pkt_bytes)

            key0 = pmt.intern("packet_len")
            val0 = pmt.from_long(p_len)
            self.add_item_tag(0,
                              self.indx,
                              key0,
                              val0
                              )
            self.indx += p_len

            i = 0
            while (i < p_len):
                output_items[0][i] = pkt_bytes[i]
                i += 1
            
            if (os.path.exists(self.confirmation_file)):
                with open(self.confirmation_file, "w") as confirm_file:
                    confirm_file.write("False")

            self.state = 0
            self.end_file_sent = True
            self.current_pkt = pkt
            self.timer.start()
            return (p_len)
        



        elif (self.state == 4):
            return (0)
        
            


            


                

        # output_items[0][:] = input_items[0] * self.example_param
        # return len(output_items[0])
