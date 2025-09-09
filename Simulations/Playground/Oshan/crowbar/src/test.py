import os
import subprocess
import time


# this file should be run inside crowbar, NOT inside src
# open with radioconda=>  gnu_scripts/testing.py --InFile="misc/message.txt" 
# wait some time (let's see how long)
# then the output.tmp should be generated inside crowbar
# then open=> strip_preamble.py output.tmp rec.txt
# the program waits 10 seconds to give strip_preamble some time then closes everythning 

base_dir = os.path.dirname(__file__)

print("=>opening the transmitter flowgraph")
path_to_gnu_script = os.path.join(base_dir, "..", "gnu_scripts", "testing.py")
gp = subprocess.Popen(["C:/Users/Oshan/radioconda/python.exe", path_to_gnu_script, "--InFile=misc/message.txt"])


print("=>waiting for 10 seconds")
time.sleep(10)
print("=>done waiting")


print("=>starting the remove the preamble")
path_to_process_file = os.path.join(base_dir, "..", "src", "strip_preamble.py")
sp = subprocess.Popen(["python", path_to_process_file, "output.tmp", "rec.txt"])


print("=>waiting for 10 seconds")
time.sleep(10)
print("=>done waiting")

print("=>closing apps")
gp.terminate()
sp.terminate()

