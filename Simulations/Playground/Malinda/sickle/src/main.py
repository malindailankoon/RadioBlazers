import os
import subprocess
import time

base_dir = os.path.dirname(__file__)



# resetting all the .txt files
f1_path = os.path.join(base_dir, "..", "userTObase", "rec_side_stuff", "misc", "confirm.txt")
with open(f1_path, "w") as f1:
    f1.write("False")

f2_path = os.path.join(base_dir, "..", "userTObase", "rec_side_stuff", "misc", "request.txt")
with open(f2_path, "w") as f2:
    f2.write("0")

f3_path = os.path.join(base_dir, "..", "baseTOuser", "rec_side_stuff", "misc", "confirm.txt")
with open(f3_path, "w") as f3:
    f3.write("False")

f4_path = os.path.join(base_dir, "..", "baseTOuser", "rec_side_stuff", "misc", "req_num.txt")
with open(f4_path, "w") as f4:
    f4.write("0")

f5_path = os.path.join(base_dir, "..", "userTObase", "rec_side_stuff", "misc", "output.tmp")
try:
    os.remove(f5_path)
except:
    pass

f6_path = os.path.join(base_dir, "..", "baseTOuser", "rec_side_stuff", "misc", "output.tmp")
try:
    os.remove(f6_path)
except:
    pass




# start oshan's receiver
path_to_oshan_script = os.path.join(base_dir, "..", "baseTOuser", "rec_side_stuff", "src", "t.py")
op = subprocess.Popen(["python", path_to_oshan_script])


time.sleep(1)

# # start hiruna's receiver
# path_to_hiruna_script = os.path.join(base_dir, "..", "userTObase", "rec_side_stuff", "src", "ACKSetup1.py")
# hp = subprocess.Popen(["python", path_to_hiruna_script])



# time.sleep(1)


# # start isitha's transmitter
# path_to_isitha_script = os.path.join(base_dir, "..", "userTObase", "gnu_scripts", "user_to_base_flowgraph.py")
# ip = subprocess.Popen(["C:/Users/immkb/radioconda/python.exe", path_to_isitha_script, "--ConFile=baseTOuser/rec_side_stuff/misc/confirm.txt", "--RnFile=baseTOuser/rec_side_stuff/misc/req_num.txt"])


# time.sleep(1)


# start malinda transmitter
path_to_malinda_script = os.path.join(base_dir, "..", "baseTOuser", "gnu_scripts", "base_to_user_flowgraph.py")
mp = subprocess.Popen(["c:\Users\jhdka\radioconda\python.exe", path_to_malinda_script, "--MsgFile=misc/message.txt", "--ConFile=userTObase/rec_side_stuff/misc/confirm.txt", "--RnFile=userTObase/rec_side_stuff/misc/request.txt"])


# time.sleep(1)

request_file = "userTObase/rec_side_stuff/misc/request.txt"
confirm_file = "userTObase/rec_side_stuff/misc/confirm.txt"

time.sleep(1)

# with open(request_file, "w") as req_file:
#     req_file.write(str(1))
# with open(confirm_file, "w") as con_file:
#     con_file.write("True")

time.sleep(240)

# for i in range(1,11):
#     with open(request_file, "w") as req_file:
#         req_file.write(str(i))
#     with open(confirm_file, "w") as con_file:
#         con_file.write("True")
#     time.sleep(3)





# time.sleep(360)


# op.terminate()
# hp.terminate()
# ip.terminate()
mp.terminate()