import os
import subprocess
import time

base_dir = os.path.dirname(__file__)


path_to_base_ui = os.path.join(base_dir, "base_station", "GUI", "base_ui.py")
ip = subprocess.Popen(["python", path_to_base_ui])



path_to_user_ui = os.path.join(base_dir, "user", "GUI", "user_ui.py")
ip = subprocess.Popen(["python", path_to_user_ui])