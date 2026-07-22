import sys
import re
from datetime import datetime


def check_med_line(line):
    # FICHCOMP med: total length 53
    errs = []
    if len(line) != 53:
        errs.append(f"length={len(line)} != 53")
    finess = line[0:9]
    # positions 9:29 = N° administratif de séjour (non contrôlé ici)
    code = line[29:38]
    nombre = line[38:45]
    date = line[45:53]
    if not finess.isdigit():
        errs.append("FINESS non numeric")
    if not code.strip().isdigit():
        errs.append("Code UCD non numeric")
    if not nombre.isdigit():
        errs.append("Nombre non numeric")
    # date: either 8 spaces or ddmmyyyy
    if date.strip():
        if not re.match(r"^\d{8}$", date):
            errs.append("Date format invalid")
        else:
            try:
                datetime.strptime(date, "%d%m%Y")
            except Exception:
                errs.append("Date non valide")
    return errs


def check_dmi_line(line):
    # FICHCOMP DMI length 50
    errs = []
    if len(line) != 50:
        errs.append(f"length={len(line)} != 50")
    finess = line[0:9]
    # positions 9:29 = N° administratif de séjour (non contrôlé ici)
    code = line[29:38]
    nombre = line[38:42]
    date = line[42:50]
    if not finess.isdigit():
        errs.append("FINESS non numeric")
    if not code.strip().isdigit():
        errs.append("Code LPP non numeric")
    if not nombre.isdigit():
        errs.append("Nombre non numeric")
    if date.strip():
        if not re.match(r"^\d{8}$", date):
            errs.append("Date format invalid")
        else:
            try:
                datetime.strptime(date, "%d%m%Y")
            except Exception:
                errs.append("Date non valide")
    return errs


def validate_file(path, typ="med"):
    total = 0
    bad = 0
    samples = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for i, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            total += 1
            errs = check_med_line(line) if typ == "med" else check_dmi_line(line)
            if errs:
                bad += 1
                if len(samples) < 10:
                    samples.append((i, line, errs))
    return {"path": path, "total": total, "bad": bad, "samples": samples}


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_fichcomp.py <file1[:type]> [file2[:type] ...]")
        sys.exit(1)
    files = sys.argv[1:]
    for f in files:
        if ":" in f:
            path, typ = f.split(":", 1)
        else:
            path, typ = f, "med"
        res = validate_file(path, typ=typ)
        print(f"{res['path']}: {res['total']} lines, {res['bad']} invalid")
        for s in res["samples"]:
            i, line, errs = s
            print(f"  line {i}: errs={errs} len={len(line)}")


if __name__ == "__main__":
    main()
