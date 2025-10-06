
def packify(data_bit_string, pkt_len):
    pkt_list = []
    number_of_packets = int(len(data_bit_string) / pkt_len)
    i = 0
    for _ in range(number_of_packets):
        pkt = data_bit_string[i:i+ pkt_len]
        pkt_list.append(pkt)
        i += 64
    return pkt_list


def depackify(pkt_list, size):
    last_data = size -  (len(pkt_list)-1) * len(pkt_list[0])
    out_data = ""
    for i in range(len(pkt_list) - 1):
        out_data += pkt_list[i]
    
    out_data += pkt_list[-1][:last_data+1]
    
    return out_data


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


pkt_len = 64
pkt_list = []

#####  IMPORTANT!!!!!!!!! the size of the message (in bits) will not exceed 12 bits


with open("misc/message.txt", "rb") as msg_file:
    data = msg_file.read()
    size = len(data) * 8
    size_bits = format(size, "012b")
    number_of_padding = (pkt_len - ((size + 12) % pkt_len)) % pkt_len    # the 12 in (size + 12) the 12 is the 12  msg size bits
    
    data_bitstring = ''.join(format(byte, "08b") for byte in data)
    padding_bitstring = "0" * number_of_padding
    
    final_bit_string = data_bitstring + padding_bitstring + size_bits

    pkt_list = packify(final_bit_string, pkt_len)
    headed_pkt_list = headify(pkt_list)

    text = deheadify(headed_pkt_list)


    

    # number_of_padding = (pkt_len - (size % pkt_len)) % pkt_len

    # print("amount of padding = ", number_of_padding)
    # print("total number of bits = ", size + number_of_padding)

    # as_int = int.from_bytes(data, "big")
    # padded_int = as_int << number_of_padding
    # total_bits = size + number_of_padding

    # padded_data = padded_int.to_bytes(total_bits // 8, "big")

    # padded_bit_string = "".join(f"{byte:08b}" for byte in padded_data)
    # pkt_list = packify(padded_bit_string, pkt_len)
    





    #---------------------------------------------------------------------------
    # with open("packets.txt", "w") as f:
    #     for pkt in pkt_list:
    #         f.write(pkt + "\n")

       
    # out_bit_string = depackify(pkt_list, size)
    # byte_list = [int(out_bit_string[i:i+8], 2) for i in range(0, len(out_bit_string), 8)]
    # data_bytes = bytes(byte_list)
    # text = data_bytes.decode("utf-8")
    # print(text)







