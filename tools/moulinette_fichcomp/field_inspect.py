import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    ln = f.readline().rstrip("\n")
    print("LEN", len(ln))
    print("Finess[0:9]", repr(ln[0:9]))
    print("Admin[9:29]", repr(ln[9:29]))
    print("Code[29:38]", repr(ln[29:38]))
    print("Nombre[38:45]", repr(ln[38:45]))
    print("Date[45:53]", repr(ln[45:53]))
