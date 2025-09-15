import os

outputReceivedFile = "output.tmp"

def seperateAndWriteToFiles(bit_string):
    address = bit_string[:2]

    request_bits = bit_string[2:8]
    request_num = int(request_bits, 2)  # convert to decimal

    # confirm received
    with open("confirmation.txt", "w") as c:
        c.write("TRUE")

    # Save request number to file
    with open("request.txt", "w") as f:
        f.write(str(request_num) + "\n")

    c.close()
    f.close()

    return request_num

def CRC_checker(bits):
  poly = 0x104C11DB7

  data = int(bits,2)

  data <<= 32

  poly_length = poly.bit_length()

  while data.bit_length() >= poly_length:
    data ^= poly << (data.bit_length() - poly_length)

  crc_bits = format(data, "032b")

  if int(crc_bits,2) !=0:
    # print("failed")
    pass
  
  else:
    # print("passed")
    seperateAndWriteToFiles(bits[:-32])
  return

def main():
    if os.path.exists(outputReceivedFile):
        # Read file in UTF-8

        with open(outputReceivedFile, "rb") as file:
            text = file.read()
        binary_string = "".join(format(b, "08b") for b in text)

        # print("Binary string:", binary_string)

        # Delete the file
        os.remove(outputReceivedFile)
        # print(f"{outputReceivedFile} deleted.")
        if (len(binary_string) != 0):
            CRC_checker(binary_string)
        
        file.close()

    else:
        # print(f"{outputReceivedFile} does not exist.")
        pass



while(1):
   main()



