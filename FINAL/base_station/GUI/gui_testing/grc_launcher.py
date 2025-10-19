import os
import subprocess
import time

base_dir = os.path.dirname(__file__)



path_to_flowgraph = os.path.join(base_dir, "interface_testing.py")

ip = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_to_flowgraph])


time.sleep(120)