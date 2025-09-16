import socket

HOST = "127.0.0.1"
my_PORT = 65433

rec_file_path = "dummy_receiving/receive.txt"

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, my_PORT))
    # print("receiver: listening...")
    while True:
        data, addr = s.recvfrom(1024)
        with open(rec_file_path, "w") as recFile:
            recFile.write(data.decode())
        