#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Title: strip_preamble
# Author: Barry Duggan

"""
Strip preamble and trailer packets from input file.
Then convert Base64 to original input.
"""

import os.path
import sys
import struct

_debug = 1          # set to zero to turn off diagnostics
state = 0
Pkt_len = 52

if (len(sys.argv) < 3):
    print ('Usage: python3 strip_preamble.py <input file> <output file>')
    print ('Number of arguments=', len(sys.argv))
    print ('Argument List:', str(sys.argv))
    exit (1)
# test if input file exists
fn = sys.argv[1]
if not(os.path.exists(fn)):
    print(fn, 'does not exist')
    exit (1)
# open input file
f_in = open (fn, 'rb')

# open output file
f_out = open (sys.argv[2], 'wb')

n_bytes = 32                                #length of in-packet preamble
preamble = bytes([0x55]) * n_bytes          #preamble
preamble_len = len(preamble)                #preamble
header_len = 10                             #size of header (fixed)
sync_word = b'%SYNC%'                       #syncword
tx_addr = 0xC001D00D                        #address we must check for
poly = 0x104C11DB7                          #crc polynomial
poly_length = poly.bit_length()             #crc polynomial length

offset = 0                                  #the position being read from on the file

message = f_in.read()

while True:
        
        #search through the message file to find the syncword
        idx = message.find(sync_word, offset)

        #eof check and close
        if idx == -1:
            break  

        print(f"Sync word found at offset {idx}")

        # Extract header right after the sync word
        header_start = idx + len(sync_word)
        header_end = header_start + header_len
        header_bytes = message[header_start:header_end] 

        seq_num, rx_addr, size = struct.unpack(">H I I", header_bytes)
        print(f"Header: seq={seq_num}, addr=0x{rx_addr:08X}, size={size}")

        if rx_addr!=tx_addr:
             print("ERROR - Wrong address")
             continue
        else:
             print("Address correct")

        data_start = header_end
        data_end = header_end + size
        data_bytes = message[data_start:data_end]

        crc_start = data_end
        #crc is 32 bits = 4 bytes
        crc_end = crc_start + 4
        data_crc_int = int.from_bytes(message[data_start:data_end], byteorder='big')
        crc_int = int.from_bytes(message[crc_start:crc_end], byteorder='big')

        if len(data_bytes) < size:
            print("Incomplete payload, stopping.")
            break

        data_crc_int <<= 32
    
        while data_crc_int.bit_length() >= poly_length:
            data_crc_int ^= poly << (data_crc_int.bit_length() - poly_length)

        data_crc_int = data_crc_int & 0xFFFFFFFF

        if data_crc_int != crc_int:
             print("CRC Error")
        else:
             print("CRC Successful")

        f_out.write(data_bytes)
        
        offset = crc_end    



f_in.close()
f_out.close()

