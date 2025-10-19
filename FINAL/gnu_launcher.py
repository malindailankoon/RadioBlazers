import os
import subprocess
import time

base_dir = os.path.dirname(__file__)



# opening the channel
path_to_channel = os.path.join(base_dir, "channel.py")

cp = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_to_channel])



# opening the client flowgraph
path_user_flowgraph = os.path.join(base_dir, "user", "gnu_stuff", "user_flowgraph.py")

up = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_user_flowgraph])


# opening the base flowgraph
path_base_flowgraph = os.path.join(base_dir, "base_station", "gnu_stuff", "base_flowgraph.py")

bp = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_base_flowgraph])