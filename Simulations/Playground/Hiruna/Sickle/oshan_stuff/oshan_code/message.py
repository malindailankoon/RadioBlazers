import os.path
import sys
import numpy as np
import struct
import time

message_file = "message.txt"
pkt_size = 64

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

timer = Stopwatch()
timer.start()

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

seq_no = 0

def headify(pkt_list):
    global seq_no
    # the header format =>     | addr - 2bits | seq_no - 6bits  | payload - 64bits | crc - 32bits |
    headed_pkt_list = []
    addr = "11" # dummy address
    for pkt in pkt_list:
        headed_pkt = ""
        headed_pkt += addr
        print(seq_no)
        seq_no_bits = format(seq_no, '06b') # convert the sequence number into 6bit bitstring
        headed_pkt += seq_no_bits
        headed_pkt += pkt
        crc_bits = crc_generator(headed_pkt)
        headed_pkt += crc_bits
        headed_pkt_list.append(headed_pkt)
        seq_no+=1
    
    return headed_pkt_list

def CRC_checker(bits):
    poly = 0x104C11DB7

    data = int(bits,2)

    data <<= 32

    poly_length = poly.bit_length()

    while data.bit_length() >= poly_length:
        data ^= poly << (data.bit_length() - poly_length)

    crc_bits = format(data, "032b")

    if int(crc_bits,2) !=0:
        return True
    else:
        return False
    
def packify(data_bit_string, pkt_len):
    pkt_list = []
    number_of_packets = int(len(data_bit_string) / pkt_len)
    i = 0
    for _ in range(number_of_packets):
        pkt = data_bit_string[i:i+ pkt_len]
        pkt_list.append(pkt)
        i += 64
    return pkt_list
    
with open(message_file, "rb") as msg_file:
                data = msg_file.read()
                msg_size = len(data) * 8

                size_bit_string = format(msg_size, "012b")

                number_of_padding = (pkt_size -((msg_size + 12) % pkt_size)) % pkt_size

                data_bitstring = ''.join(format(byte, "08b") for byte in data)
                padding_bitstring = '0' * number_of_padding

                final_bitstring = data_bitstring + padding_bitstring + size_bit_string

                pkt_list = packify(final_bitstring, pkt_size)

                payload_list = headify(pkt_list)


while True:
     
          time.sleep(5)
          if len(payload_list) <= 0:
               break
          with open("output.tmp","wb") as output:
                current_pkt = payload_list.pop(0)
                pkt_bytes = np.packbits(np.frombuffer(current_pkt.encode("ascii"), dtype=np.uint8) - 48)
                output.write(pkt_bytes)
    