import os.path
import sys
import numpy as np
import struct
import subprocess

state = 0
addr = "11"
base_dir = os.path.dirname(__file__)
path_to_output_tmp = os.path.join(base_dir, "..", "misc", "output.tmp")
request_file = os.path.join(base_dir, "..", "misc", "req_num.txt") # '../misc/req_num.txt' 
confirm_file = os.path.join(base_dir, "..", "misc", "confirm.txt") # '../misc/confirm.txt' 
output_file = os.path.join(base_dir, "..", "misc", "final.txt") # '../misc/final.txt'
# message_file = "message.txt"
req = 0
packet = ''
pkt_size = 64
end_file_delimiter = "1010101010101010101010101010101010101010101010101010101010101010"
headed_pkt_list = []


## CODE FOR TESTING!
testing_req_file = os.path.join(base_dir, "..", "..", "..", "userTObase", "rec_side_stuff", "misc", "request.txt")
testing_con_file = os.path.join(base_dir, "..", "..", "..", "userTObase", "rec_side_stuff", "misc", "confirm.txt")
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


print("oshan program started!")





while True:

    if (state == 0):
        
        try:
            with open(path_to_output_tmp,"rb") as data:
                # print("file_found!")
                packet = data.read(13)
            packet_size = len(packet)
            if packet_size < 13:
                #change to state = 0 if there are errors in the ACK
                state = 0
            else:
                state = 1
        except:
            
            state = 0
    
    if (state == 1):
        print("oshan: state 1 started")
        packet_bitstring = ''.join(format(byte, "08b") for byte in packet)
        print(packet_bitstring)
        rx_crc_string = packet_bitstring[-32:]
        header_string = packet_bitstring[:8]
        payload_string = packet_bitstring[8:-32]

        if (int(crc_generator(packet_bitstring)) != 0):
            # print(crc_generator(packet_bitstring))
            # print(int(crc_generator(packet_bitstring)))
            print('CRC Failed')
            state = 2
            continue
        else:
            print("CRC successful")
            # print(crc_generator(packet_bitstring))
            # print(int(crc_generator(packet_bitstring)))

        rx_addr = header_string[:2]   # "110110"
        rx_seq = header_string[2:8]
        # print(rx_seq)
        # print(int(rx_seq,2))

        print(type(rx_addr))
        print(header_string)
        if rx_addr != addr: 
            print("Incorrect Address")
            state = 0
            continue
        
        if req == int(rx_seq,2):
            req += 1
            state = 2
            with open(request_file, "w") as req_file:
                req_file.write(str(req))
            
            # TESTING CODE ----------------------
            with open(testing_req_file, "w") as tf:
                tf.write(str(req))
            # ----------------------------------
            
            print("received payload packet => ", payload_string)
            if (payload_string == end_file_delimiter):
                break
            else:
                headed_pkt_list.append(payload_string)

            # payload_bytes = np.packbits(np.frombuffer(payload_string.encode("ascii"), dtype=np.uint8) - 48)
            # with open(output_file, "ab") as final:
            #     final.write(payload_bytes)
            continue
        else:
            state = 2
            print("incorrect seq number")
            continue

    if (state == 2):
        print("oshan: state 2 started")
        print("Sending ACK for ", req)
        with open(confirm_file, "w") as conf:
            conf.write("True")
        
        #  TESTING CODE----------------
        with open(testing_con_file, "w") as cf:
            cf.write("True")
        # ----------------------------
        # print("clearing output.tmp")
        with open(path_to_output_tmp, "w") as f:
            pass
        # os.remove(path_to_output_tmp)
        state = 0


text = deheadify(headed_pkt_list)
with open(output_file, "w") as out_file:
    out_file.write(text)