import subprocess
import os
import socket


print("opening the gnu interface...")
basedir = os.path.dirname(__file__)
script_path = os.path.join(basedir, "..", "gnu_scripts", "testing2.py")
gp = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", script_path])

print("opening receiver interface...")
rec_file_path = "src/receiver_v2.py"
rp = subprocess.Popen(["python", rec_file_path])




HOST = "127.0.0.1"
gnu_dest_PORT = 60000

message_file_path = "to_be_transmitted/message.txt"

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    while True:
        msg = input("press ENTER to transmit the message, type q or quit to quit")
        if msg == "quit" or msg=="q":
            break
        with open(message_file_path, "r") as msg_file:
            data = msg_file.read()
            s.sendto(data.encode(), (HOST, gnu_dest_PORT))




print("closing app")
gp.terminate()
rp.terminate()