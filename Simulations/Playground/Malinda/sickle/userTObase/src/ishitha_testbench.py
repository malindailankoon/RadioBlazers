import os
import subprocess
import time



base_dir = os.path.dirname(__file__)
i = 1

path_to_gnu_tx_script = os.path.join(base_dir, "..", "gnu_scripts", "user_to_base_flowgraph.py")

gtp = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_to_gnu_tx_script, "--ConFile=userTObase/misc/confirm.txt", "--RnFile=userTObase/misc/req_number.txt"])


time.sleep(5)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)


with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

with open("userTObase/misc/req_number.txt", "w") as req_file:
    req_file.write(str(i))
with open("userTObase/misc/confirm.txt", "w") as con_file:
    con_file.write("True")
i += 1
time.sleep(2)

gtp.terminate()