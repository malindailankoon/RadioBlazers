import os.path
import sys
import numpy as np
import struct
import subprocess

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

    
packet_bitstring = '11000000011100100110100101101110011001010111001100100000011000010111001010100010100100100001110101100011'
og_packet = packet_bitstring[:-32]
og_crc = packet_bitstring[-32:]

print(crc_generator(packet_bitstring))
print(type(crc_generator(packet_bitstring)))


