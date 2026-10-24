#!/usr/bin/env python3
"""ตรวจสายตามรอยทั้งระบบ EV ถึง REQ ถึง UC ถึง AC ถึง test (UC-01 ถึง UC-14) และเขียน docs/srs/rtm-all.md ใหม่

ใช้: python3 scripts/check_rtm.py          (ตรวจและเขียนไฟล์ ถ้ามีสายขาด exit 1)
     python3 scripts/check_rtm.py --check  (ตรวจอย่างเดียว ไม่เขียนไฟล์)

อ่านจาก
- AC: ทุก scenario ใน specs/*/*.feature (ป้าย @AC-xx-yy และ @REQ-... บนบรรทัดก่อน Scenario)
- REQ: docs/srs/catalogue.md, docs/srs/catalogue-other.md, specs/000-shared/constraints.md (ข้อที่มีหัวข้อ ### REQ-)
- ที่มาของ REQ: คอลัมน์ "ที่มา" ใน catalogue.md (EV-xxx หรือที่มาอื่นที่บันทึกไว้ เช่น MD- TOR OWASP PDPA)
- test: backend/tests/*.py (def test_AC_xx_yy...) และ frontend/src/__tests__/*.test.jsx (ชื่อไฟล์หรือชื่อ test มี AC-xx-yy)
- UC: เลขกลางของ AC (AC-07-nn เป็นของ UC-07) ยกเว้น AC-00 (ข้ามทุก feature) UC-03 UC-06 เป็นขั้นของ UC-07 ตามตาราง INCLUDED
สายขาด = UC ไม่มี AC | AC ไม่มีป้าย REQ | REQ ที่ AC อ้างไม่มีในบัญชี | REQ ไม่มีที่มา | AC ไม่มี test | REQ Approved ใน catalogue ไม่มี AC และไม่อยู่ใน NO_AC
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UCS = [f"UC-{i:02d}" for i in range(1, 15)]
INCLUDED = {"UC-03": ["AC-07-02", "AC-07-08"], "UC-06": ["AC-07-01", "AC-07-05", "AC-07-06", "AC-07-12", "AC-07-13"]}
# REQ ที่ตรวจด้วยวิธีอื่นที่ไม่ใช่ AC (บันทึกเหตุผลไว้ที่ต้นทาง)
NO_AC = {
    "REQ-OP-006": "ตรวจด้วย walkthrough ของคู่มือ (EV-045) และ OAT-3",
    "REQ-CMP-001": "ตรวจด้วย inspection ของ SH-05",
    "REQ-CON-001": "ข้อจำกัดของแผนโครงการ ตรวจใน plan ข้อ 7 ของทุก feature",
    "REQ-CON-003": "ข้อจำกัดของสัญญา ตรวจผ่าน AC ของ IF-01",
    "REQ-AI-002": "Won't",
    "REQ-SEC-004": "ตรวจด้วย AC-07-09 AC-09-09 (ป้ายอยู่ที่ REQ-PRV-002)",
}
SOURCE_OK = re.compile(r"Operations|EV-\d{3}|MD-|TOR|OWASP|PDPA|Q-\d{2}|GAP-\d{2}|F-\d{2}|UC-\d{2}|SH-\d{2}|สัญญา|แผนโครงการ|CR-\d{2}|ASI|EU AI Act|หน้าบทเรียน|derived|DR-\d{2}|OAT")


def features():
    acs = {}
    for f in sorted(ROOT.glob("specs/*/*.feature")):
        tags = []
        for line in f.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("@"):
                tags = s.split()
            elif s.startswith("Scenario"):
                ids = [t[1:] for t in tags if t.startswith("@AC-")] or re.findall(r"AC-\d{2}-\d{2}", s)
                reqs = [t[1:] for t in tags if t.startswith("@REQ-")]
                for a in ids:
                    acs[a] = {"feature": f.relative_to(ROOT).as_posix(), "reqs": reqs, "title": s.split(":", 1)[-1].strip()}
                tags = []
    return acs


def catalogue():
    reqs = {}
    for name in ("docs/srs/catalogue.md", "docs/srs/catalogue-other.md"):
        p = ROOT / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\| (REQ-[A-Z]+-\d{3}) \|(.*)\|\s*$", line)
            if m:
                cols = [c.strip() for c in m.group(2).split("|")]
                status = cols[3] if len(cols) > 3 else ""
                src = cols[4] if len(cols) > 4 else ""
                reqs.setdefault(m.group(1), {"status": status, "source": src, "file": name})
    for line in (ROOT / "specs/000-shared/constraints.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (REQ-[A-Z]+-\d{3})", line)
        if m:
            reqs.setdefault(m.group(1), {"status": "Approved", "source": "constraints.md", "file": "specs/000-shared/constraints.md"})
            if reqs[m.group(1)]["source"] in ("", "constraints.md"):
                reqs[m.group(1)]["source"] = "Constraint กลาง (ที่มาในไฟล์กลาง)"
    return reqs


def tests():
    found = defaultdict(list)
    for p in sorted(ROOT.glob("backend/tests/*.py")):
        for m in re.finditer(r"def (test_AC_\w*)", p.read_text(encoding="utf-8")):
            name = m.group(1)
            ids = set()
            for g in re.finditer(r"AC_(\d{2})((?:_\d{2})+)", name):   # test_AC_13_02_03_04 = AC-13-02, 03, 04
                ids |= {f"AC-{g.group(1)}-{n}" for n in re.findall(r"\d{2}", g.group(2))}
            for a in ids:
                found[a].append(f"{p.name}::{name}")
    for p in sorted(ROOT.glob("frontend/src/__tests__/*.test.jsx")):
        text = p.read_text(encoding="utf-8")
        ids = set(re.findall(r"AC-\d{2}-\d{2}", p.name))
        ids |= set(re.findall(r"test\('(AC-\d{2}-\d{2})", text))
        for a in ids:
            found[a].append(p.name)
    return found


def main():
    acs, reqs, tst = features(), catalogue(), tests()
    broken, by_uc = [], defaultdict(list)
    for a, info in acs.items():
        uc = "UC-" + a[3:5]
        by_uc[uc].append(a)
        if not info["reqs"]:
            broken.append(f"{a} ไม่มีป้าย REQ ({info['feature']})")
        for r in info["reqs"]:
            if r not in reqs:
                broken.append(f"{a} อ้าง {r} ที่ไม่มีในบัญชี")
        if not tst.get(a):
            broken.append(f"{a} ไม่มี test")
    for uc, lst in INCLUDED.items():
        by_uc[uc] = [a for a in lst if a in acs]
    for uc in UCS:
        if not by_uc.get(uc):
            broken.append(f"{uc} ไม่มี AC")
    used = {r for i in acs.values() for r in i["reqs"]}
    for r, info in reqs.items():
        if (info["file"] != "docs/srs/catalogue-other.md" or r in used) and not SOURCE_OK.search(info["source"]) \
                and "Constraint กลาง" not in info["source"]:
            broken.append(f"{r} ไม่มีที่มา ({info['file']})")
        if info["file"] == "docs/srs/catalogue.md" and info["status"].startswith("Approved") and r not in used and r not in NO_AC:
            broken.append(f"{r} Approved แต่ไม่มี AC")
    for r in sorted(used - set(reqs)):
        pass  # รายงานแล้วรายข้อข้างบน
    if "--check" not in sys.argv:
        write(acs, reqs, tst, by_uc, used, broken)
    print(f"AC {len(acs)} ข้อ | REQ ในบัญชี {len(reqs)} ข้อ REQ ที่ AC อ้าง {len(used)} ข้อ | UC {sum(1 for u in UCS if by_uc.get(u))} จาก 14")
    print(f"AC ที่มี test {sum(1 for a in acs if tst.get(a))} จาก {len(acs)}")
    if broken:
        print("สายขาด:")
        for b in broken:
            print(" ", b)
        return 1
    print("สายขาด: 0")
    return 0


def evs(src):
    return ", ".join(sorted(set(re.findall(r"EV-\d{3}", src)))) or src[:60]


def write(acs, reqs, tst, by_uc, used, broken):
    out = ["# ตารางตามรอยทั้งระบบ (EV ถึง REQ ถึง UC ถึง AC ถึง test) Baseline B7", "",
           "ไฟล์นี้สร้างโดย scripts/check_rtm.py ห้ามแก้ด้วยมือ รันใหม่ทุกครั้งที่ .feature catalogue หรือ test เปลี่ยน",
           "rtm.md ของแต่ละ feature ยังเป็นที่ของการตามรอยถึง task โค้ด หน้าจอ ข้อค้นพบ และช่อง \"ทีมตัดสิน\" ไฟล์นี้ตรวจเฉพาะว่าสายไม่ขาด", "",
           f"สรุป: UC {sum(1 for u in UCS if by_uc.get(u))} จาก 14 | AC {len(acs)} ข้อ มี test {sum(1 for a in acs if tst.get(a))} ข้อ | REQ ที่ AC อ้าง {len(used)} ข้อ | สายขาด {len(broken)}", "",
           "## 1. ราย use case", "", "| UC | AC | REQ ที่ AC อ้าง | ที่มา (EV) ของ REQ เหล่านั้น |", "|---|---|---|---|"]
    for uc in UCS:
        lst = sorted(by_uc.get(uc, []))
        rq = sorted({r for a in lst for r in acs[a]["reqs"]})
        ev = sorted({e for r in rq for e in re.findall(r"EV-\d{3}", reqs.get(r, {}).get("source", ""))})
        span = ", ".join(lst) if uc in INCLUDED else f"{lst[0]} ถึง {lst[-1]}" if lst else ""
        out.append(f"| {uc} | {len(lst)} ข้อ ({span}) | {', '.join(rq)} | {', '.join(ev) or 'ที่มาเป็นโมเดลหรือข้อจำกัด'} |" if lst else f"| {uc} | ไม่มี | | |")
    out += ["", "AC-00 (ข้ามทุก feature) ไม่ใช่ของ use case ใด อยู่ในส่วน 2 ด้วย", "",
            "## 2. ราย AC", "", "| AC | UC | REQ | test |", "|---|---|---|---|"]
    for a in sorted(acs):
        uc = "ข้ามทุก feature" if a.startswith("AC-00") else "UC-" + a[3:5]
        out.append(f"| {a} | {uc} | {', '.join(acs[a]['reqs'])} | {'; '.join(tst.get(a, [])) or 'ไม่มี'} |")
    out += ["", "## 3. ราย REQ (ที่มา และ AC)", "", "| REQ | ที่มา | AC |", "|---|---|---|"]
    rev = defaultdict(list)
    for a, i in acs.items():
        for r in i["reqs"]:
            rev[r].append(a)
    for r in sorted(reqs):
        if reqs[r]["file"] == "docs/srs/catalogue-other.md" and r not in rev:
            continue
        ac = ", ".join(sorted(rev.get(r, []))) or NO_AC.get(r, "ไม่มี")
        out.append(f"| {r} | {evs(reqs[r]['source'])} | {ac} |")
    out += ["", "## 4. สายขาด", ""] + ([f"- {b}" for b in broken] or ["ไม่มี"])
    (ROOT / "docs/srs/rtm-all.md").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
