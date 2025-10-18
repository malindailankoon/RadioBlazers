

int_arr = [170, 0, 127, 255] # this would be what pmt.u8vector_elements(vec) returns
# can convert the int_arr back to a u8vector using 
# u8 = pmt.init_u8vector(len(int_arr), int_arr)

def byte_list_to_bitstring(int_arr):
    return ''.join(f'{b:08b}' for b in int_arr)


def bit_string_to_byte_list(bits):
    if len(bits) % 8 != 0:
        raise ValueError("length not multiple of 8")
    return [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]



msg = "Hii, my name is malinda."

def msg_string_to_bitstring(msg_str):
    bits = ''.join(f'{b:08b}' for b in msg_str.encode('utf-8'))
    return bits

def bitstring_to_text(bits, encoding='utf-8'):
    if len(bits) % 8 != 0:
        raise ValueError("Bitstring length must be a multiple of 8")
    data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return data.decode(encoding)


print(msg.encode("utf-8"))
