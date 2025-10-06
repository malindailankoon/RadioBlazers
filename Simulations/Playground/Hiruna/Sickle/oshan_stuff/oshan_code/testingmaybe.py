import subprocess
import time

message_proc = subprocess.Popen(["python", "message.py"])

time.sleep(6)

t_proc = subprocess.Popen(["python", "t.py"])

time.sleep(30)

message_proc.terminate()
t_proc.terminate()

