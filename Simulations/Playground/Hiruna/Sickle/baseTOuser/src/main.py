import subprocess
import os
import time



base_dir = os.path.dirname(__file__)

path_to_gnu_tx_script = os.path.join(base_dir, "..", "gnu_scipts", "pickaxe_flowgraph.py")

gtp = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_to_gnu_tx_script, "--PktFile=misc/packets.txt", "--ConFile=misc/confirm.txt"])



time.sleep(4)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(3)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(3)
with open("misc/confirm.txt", "w") as f:
    f.write("True")

time.sleep(3)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")


time.sleep(1)
with open("misc/confirm.txt", "w") as f:
    f.write("True")








gtp.terminate()