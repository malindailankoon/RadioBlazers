

with open("misc/test.txt", "r") as f:
    d = f.read().strip()

    i = int(d)
    print(i+1)