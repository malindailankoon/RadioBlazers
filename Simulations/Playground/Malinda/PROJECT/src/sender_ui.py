import subprocess
import os


while True:
    msg = input("press ENTER to transmit message, type q or quit to quit")
    if msg == "quit" or msg=="q":
        break
    file_path = "to_be_transmitted/message.txt"
    chat_log_file_path = "chat_logs/send_logs.txt"
    if msg == "":
        # with open(file_path, "w") as file:
        #     file.write(msg)
        
        # with open(chat_log_file_path, "a") as logfile:
        #     logfile.write(msg + "\n")
        
        basedir = os.path.dirname(__file__)
        script_path = os.path.join(basedir, "..", "gnu_scripts", "testing.py")
        subprocess.run(["C:/Users/immkb/radioconda/python.exe", script_path])

