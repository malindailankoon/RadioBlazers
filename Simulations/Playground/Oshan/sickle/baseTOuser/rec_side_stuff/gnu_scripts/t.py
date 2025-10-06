import os.path
import sys
import numpy as np
import struct

state = 0
addr = "11"
request_file = "D:\Important Files\University\Files\Sem 3\EN2130 - Communication Design Project\CDP_PythonCode\RadioBlazers\Simulations\Playground\Oshan\sickle\baseTOuser\misc\req_num.txt"
confirm_file = "D:\Important Files\University\Files\Sem 3\EN2130 - Communication Design Project\CDP_PythonCode\RadioBlazers\Simulations\Playground\Oshan\sickle\baseTOuser\misc\confirm.txt"
output_file = "D:\Important Files\University\Files\Sem 3\EN2130 - Communication Design Project\CDP_PythonCode\RadioBlazers\Simulations\Playground\Oshan\sickle\baseTOuser\misc\final.txt"
req = 0
packet = ''

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

while True:

    if (state == 0):
        try:
            with open("output.tmp","rb") as data:
                packet = data.read()
            packet_size = len(packet.read())
            if packet_size < 13:
                state = 2
            else:
                state = 1
        except:
            print("File does not exist")
    
    if (state == 1):
        packet_bitstring = ''.join(format(byte, "08b") for byte in packet)
        rx_crc_string = packet_bitstring[-32:]
        header_string = packet_bitstring[:8]
        payload_string = packet_bitstring[8:-32]

        if CRC_checker(packet_bitstring):
            state = 2
            continue

        rx_addr = header_string[:2]   # "110110"
        rx_seq = header_string[2:8]

        if rx_addr != addr: 
            print("Incorrect Address")
            state = 0
            continue
        
        if req == int(rx_seq):
            req += 1
            state = 2
            with open(request_file, "w") as req_file:
                req_file.write(str(req))
            payload_bytes = np.packbits(np.frombuffer(payload_string.encode("ascii"), dtype=np.uint8) - 48)
            with open(output_file, "wb") as final:
                final.write(payload_bytes)
            continue
        else:
            state = 2
            continue

    if (state == 2):
        with open(confirm_file, "w") as conf:
            conf.write("True")
        os.remove("output.tmp")
        state = 0
            

            

