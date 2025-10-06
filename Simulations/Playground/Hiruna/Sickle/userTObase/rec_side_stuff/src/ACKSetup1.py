import os



base_dir = os.path.dirname(__file__)

outputReceivedFile = os.path.join(base_dir, "..", "misc", "output.tmp") # "../misc/output.tmp"
confirm_file = os.path.join(base_dir, "..", "misc", "confirm.txt") # "../misc/confirm.txt"
request_file = os.path.join(base_dir, "..", "misc", "request.txt") # "../misc/request.txt"

def seperateAndWriteToFiles(bit_string):
    address = bit_string[:2]

    request_bits = bit_string[2:8]
    request_num = int(request_bits, 2)  # convert to decimal

    # confirm received
    with open(confirm_file, "w") as c:
        c.write("TRUE")

    # Save request number to file
    with open(request_file, "w") as f:
        f.write(str(request_num))

    c.close()
    f.close()

    return request_num

def crc_generator(bits): 
    poly = 0x104C11DB7

    data = int(bits,2)

    data <<= 32

    poly_length = poly.bit_length()

    while data.bit_length() >= poly_length:
        data ^= poly << (data.bit_length() - poly_length)

    crc_bits = format(data, "032b")
    # print(len(bits), len(crc_bits))
    return crc_bits  



print("hiruna program started!")


while (True):
    if os.path.exists(outputReceivedFile):

        with open(outputReceivedFile, "rb") as file:
            text = file.read()
            if (len(text) < 5):
                continue
        bitstring = ''.join(format(byte, "08b") for byte in text)

        os.remove(outputReceivedFile)
        
        if int(crc_generator(bitstring)) == 0:
            seperateAndWriteToFiles(bitstring)
        else:
            pass
            
    else:
        # print(f"{outputReceivedFile} does not exist.")
        pass







