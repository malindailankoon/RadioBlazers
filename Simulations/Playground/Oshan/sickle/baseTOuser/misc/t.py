import os.path
import sys
import numpy as np
import struct
import subprocess

state = 0
addr = "11"
request_file = 'req_num.txt' 
confirm_file = 'confirm.txt' 
output_file = 'final.txt'
message_file = "message.txt"
req = 0
packet = ''
pkt_size = 64

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

while True:

    if (state == 0):
        try:
            with open("output.tmp","rb") as data:
                packet = data.read()
            packet_size = len(packet)
            if packet_size < 13:
                #change to state = 0 if there are errors in the ACK
                state = 2
            else:
                state = 1
        except:
            state = 0
    
    if (state == 1):
        packet_bitstring = ''.join(format(byte, "08b") for byte in packet)
        rx_crc_string = packet_bitstring[-32:]
        header_string = packet_bitstring[:8]
        payload_string = packet_bitstring[8:-32]

        if (int(crc_generator(packet_bitstring)) != 0):
            print(crc_generator(packet_bitstring))
            print(int(crc_generator(packet_bitstring)))
            print('CRC Failed')
            state = 2
            continue
        else:
            print("CRC successful")
            print(crc_generator(packet_bitstring))
            print(int(crc_generator(packet_bitstring)))

        rx_addr = header_string[:2]   # "110110"
        rx_seq = header_string[2:8]
        print(rx_seq)
        print(int(rx_seq,2))

        if rx_addr != addr: 
            print("Incorrect Address")
            state = 0
            continue
        
        if req == int(rx_seq,2):
            req += 1
            state = 2
            with open(request_file, "w") as req_file:
                req_file.write(str(req))
            payload_bytes = np.packbits(np.frombuffer(payload_string.encode("ascii"), dtype=np.uint8) - 48)
            with open(output_file, "ab") as final:
                final.write(payload_bytes)
            continue
        else:
            state = 2
            continue

    if (state == 2):
        print("Sending ACK for ", req)
        with open(confirm_file, "w") as conf:
            conf.write("True")
        print("Deleting output.tmp")
        os.remove("output.tmp")
        state = 0


