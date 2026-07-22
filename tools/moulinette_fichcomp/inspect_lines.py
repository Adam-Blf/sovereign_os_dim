import sys


def show(path, n=5):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i in range(n):
            line = f.readline()
            if not line:
                break
            s = line.rstrip("\n")
            print(f"{i + 1}: LEN={len(s)} | {repr(s)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inspect_lines.py <file> [n]")
        sys.exit(1)
    path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    show(path, n)
