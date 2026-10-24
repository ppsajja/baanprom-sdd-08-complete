"""รัน eval ของผู้ช่วย UC-14 แล้วเขียนผลลง specs/005-ai-assistant/ (CR-09, T-09 ของ 005)
ใช้: python eval_run.py [--prompt-version P-1.1] [--out ../specs/005-ai-assistant/eval-results.md]
อ่าน eval set ทั้ง 3 ชุดใน specs/005-ai-assistant/eval/ รันผ่าน MockLLM (ตัวจริงยังไม่ต่อ IF-05)
แล้วรันซ้ำแบบปิดรั้วขาออก เพื่อดูว่ารั้วกันอะไรไว้บ้าง (ผลส่วนนี้ไม่นับเป็นเกณฑ์)
คืนรหัส 0 เมื่อผ่านทุกเกณฑ์ 1 เมื่อมีเกณฑ์ไม่ผ่าน (ใช้ใน CI ได้แบบเดียวกับ pytest)"""
import argparse
import json
import os
import platform
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")

from app import config  # noqa: E402
from app.assistant import evaluation as ev  # noqa: E402
from app.assistant.llm import MockLLM  # noqa: E402

SPEC = Path(__file__).resolve().parent.parent / "specs" / "005-ai-assistant"


def heldout_ids() -> set[str]:
    """CR-19: ชุดลับของผู้ว่าจ้าง (TOR ภาคผนวก ค) 50 ข้อจาก 200"""
    path = SPEC / "eval" / "heldout.json"
    return set(json.loads(path.read_text(encoding="utf-8"))["ids"]) if path.exists() else set()


def eval_versions() -> dict:
    out = {}
    for name in ("qa", "reschedule", "injection"):
        out[name] = sorted({i["version"] for i in ev.load(name)})
    return out


def md_report(res: dict, diag: dict, version: str, started: str, seconds: float) -> str:
    s = res["summary"]
    L = []
    L.append(f"# ผล eval ของผู้ช่วย UC-14 รุ่นข้อความสั่ง {version}")
    L.append("")
    L.append(f"ไฟล์นี้เขียนโดย backend/eval_run.py ห้ามแก้ด้วยมือ | รันเมื่อ {started} | ใช้เวลา {seconds:.1f} วินาที | "
             f"Python {platform.python_version()}")
    L.append(f"โมเดล: {MockLLM.model_version} (MockLLM ตัวจริงยังไม่ต่อ IF-05) | eval set: qa {res['sizes']['qa']} ข้อ "
             f"reschedule {res['sizes']['reschedule']} ข้อ injection {res['sizes']['injection']} ข้อ | รุ่นของ eval set {eval_versions()}")
    L.append(f"คำสั่ง: cd backend && python eval_run.py --prompt-version {version}")
    L.append("")
    L.append(f"สรุป: {'ผ่านทุกเกณฑ์' if s['all_pass'] else 'มีเกณฑ์ไม่ผ่าน'} "
             f"({sum(c['pass'] for c in s['criteria'])} จาก {len(s['criteria'])} เกณฑ์)")
    L.append("")
    L.append("## 1. เกณฑ์ตาม AC")
    L.append("")
    L.append("| AC | เกณฑ์ | ได้ | จาก | เกณฑ์ผ่าน | ชนิด | ผล |")
    L.append("|---|---|---|---|---|---|---|")
    kind = {"abs": "เด็ดขาด", "ratio": "สัดส่วน ไม่ต่ำกว่า", "max": "ไม่เกิน"}
    for c in s["criteria"]:
        L.append(f"| {c['ac']} | {c['name']} | {c['got']} | {c['total']} | {c['need']} | {kind[c['kind']]} | "
                 f"{'ผ่าน' if c['pass'] else 'ไม่ผ่าน'} |")
    L.append("")
    L.append("เกณฑ์ที่ eval อัตโนมัติวัดไม่ได้ (ต้องใช้คน) ยังไม่ได้วัด: AC-14-03 คนตรวจ 30 ข้อสุ่ม \"อ่านง่ายและสุภาพ\" ไม่ต่ำกว่า 27 ใน 30 "
             "(ตัวอย่างอยู่ในส่วน 5) | AC-14-09 ลูกค้าจริง 20 คนเข้าใจสรุป ไม่ต่ำกว่า 18 ใน 20 | AC-14-12 ผู้ใช้ทดสอบ 20 คนรู้ว่าเป็น AI "
             "ไม่ต่ำกว่า 19 ใน 20 | QAS-1 ค่าเรียก LLM ต่อคำถาม (MockLLM ไม่มีค่าใช้จ่าย) และ p95 ที่วัดได้เป็นเวลาของโค้ดเราเท่านั้น")
    L.append("")
    L.append("## 2. แยกกลุ่ม (REQ-AI-021)")
    L.append("")
    L.append("| กลุ่ม | จำนวนข้อ | ถูกและครบ ต่อ 100 | ส่งต่อเพราะไม่แน่ใจ | ต่อ 100 | เท่าของค่ารวม |")
    L.append("|---|---|---|---|---|---|")
    for g in s["groups"]:
        L.append(f"| {g['group']} | {g['n']} | {g.get('complete_per_100', '')} | {g.get('unclear_handoff', '')} | "
                 f"{g.get('rate_per_100', '')} | {g.get('times_overall', '')} |")
    L.append("")
    L.append("## 3. รั้วกันอะไรไว้ (REQ-AI-008)")
    L.append("")
    blocked = Counter()
    for r in res["qa"] + res["injection"]:
        if r.guard.startswith("blocked:"):
            for x in r.guard.split(":", 1)[1].split(","):
                blocked[x] += 1
    L.append("รั้วขาออกกันคำตอบของ LLM แล้วใช้คำตอบสำรองจากโค้ด: " +
             (" | ".join(f"{k} {v} ครั้ง" for k, v in sorted(blocked.items())) or "ไม่มี"))
    stops = Counter(r.notes.get("stopped_at") for r in res["injection"])
    names = {"inbound": "รั้วขาเข้ากัน", "outbound": "รั้วขาออกกัน", "not_reached_llm": "กฎขั้นจำแนกหรือขั้นค้นข้อมูลกันก่อนถึง LLM",
             "llm_not_obeyed": "ถึง LLM แต่ข้อความหลอกถูกตัดออกจากข้อมูลแล้ว (ขั้นค้นข้อมูล)"}
    L.append("ชุดข้อความหลอกให้ลืมกฎ 30 ข้อ หยุดที่: " + " | ".join(f"{names.get(k, k)} {v} ข้อ" for k, v in sorted(stops.items())))
    L.append("")
    L.append("ทดลองปิดรั้วขาออก (รันซ้ำทั้งชุด ไม่นับเป็นเกณฑ์ ใช้ดูคุณค่าของรั้ว):")
    for c in diag["summary"]["criteria"]:
        if c["kind"] == "abs" and not c["pass"]:
            L.append(f"- {c['ac']} {c['name']}: {c['got']} จาก {c['total']}")
    if all(c["pass"] for c in diag["summary"]["criteria"] if c["kind"] == "abs"):
        L.append("- ไม่มีเกณฑ์เด็ดขาดที่ตก")
    L.append("")
    L.append("## 3.1 ชุดลับ 50 ข้อ (TOR ของ R2 ภาคผนวก ค ผู้รับจ้างไม่เคยเห็น)")
    L.append("")
    held = heldout_ids()
    hq = [r for r in res["qa"] if r.id in held]
    L.append(f"รายการข้ออยู่ใน specs/005-ai-assistant/eval/heldout.json | ข้อในชุดลับ {len(hq)} ข้อ | ถูกและครบ "
             f"{sum(1 for r in hq if r.complete)} จาก {len(hq)} | เด็ดขาดไม่ผ่าน {sum(1 for r in hq if r.absolute_fail)} ข้อ "
             f"| ชุดที่ผู้รับจ้างเห็น {len(res['qa']) - len(hq)} ข้อ ถูกและครบ {sum(1 for r in res['qa'] if r.id not in held and r.complete)}")
    L.append("ใช้เทียบว่าผลบนชุดลับไม่ต่ำกว่าชุดที่เห็นอย่างมีนัย (ถ้าต่ำกว่ามาก แปลว่าระบบถูกปรับให้จำคำตอบของชุดที่เห็น)")
    L.append("")
    L.append("## 4. ข้อที่ไม่ \"ถูกและครบ\"")
    L.append("")
    L.append("| ข้อ | ชุด | หมวด | การพิมพ์ | ผล | เหตุ | คำตอบ |")
    L.append("|---|---|---|---|---|---|---|")
    for r in res["qa"] + res["reschedule"] + res["injection"]:
        if not r.complete:
            why = ",".join(r.absolute_fail) or ("พฤติกรรมไม่ตรง" if not r.behavior_ok else "ไม่ครบตามกติกาคำตอบ")
            L.append(f"| {r.id} | {r.set} | {r.category} | {r.labels['typing']} | {r.outcome} | {why} | "
                     f"{r.reply[:120].replace('|', '/')} |")
    L.append("")
    L.append("## 5. ตัวอย่าง 30 ข้อสำหรับคนตรวจตามใบให้คะแนน (eval/human-rubric.md) สุ่มด้วย seed 14")
    L.append("")
    L.append("คนตรวจเติมช่อง \"ผ่าน 5 ข้อ\" เอง (ยังไม่ได้ตรวจ) ผลนี้คือเกณฑ์บรรทัดที่ 3 ของ AC-14-03")
    L.append("")
    L.append("| ข้อ | คำถาม | คำตอบ | ผ่าน 5 ข้อ |")
    L.append("|---|---|---|---|")
    qa_items = {i["id"]: i for i in ev.load("qa")}
    for r in random.Random(14).sample(res["qa"], 30):
        L.append(f"| {r.id} | {qa_items[r.id]['question']} | {r.reply.replace('|', '/')} | |")
    L.append("")
    return "\n".join(L)


def to_json(res: dict) -> dict:
    def row(r):
        return {"id": r.id, "set": r.set, "category": r.category, "labels": r.labels, "outcome": r.outcome,
                "complete": r.complete, "absolute_fail": r.absolute_fail, "guard": r.guard, "reply": r.reply,
                "latency_ms": round(r.latency_ms, 2), "notes": r.notes}
    return {"version": res["version"], "sizes": res["sizes"], "summary": res["summary"],
            "results": [row(r) for r in res["qa"] + res["reschedule"] + res["injection"]]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-version", default=config.assistant_prompt_version())
    ap.add_argument("--out", default=str(SPEC / "eval-results.md"))
    a = ap.parse_args()
    started = datetime.now().strftime("%Y-%m-%d %H:%M")
    t0 = datetime.now()
    res = ev.run_all(a.prompt_version)
    diag = ev.run_all(a.prompt_version, use_output_guard=False)
    seconds = (datetime.now() - t0).total_seconds()
    out = Path(a.out)
    out.write_text(md_report(res, diag, a.prompt_version, started, seconds), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(to_json(res), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    s = res["summary"]
    print(f"prompt {a.prompt_version}: {sum(c['pass'] for c in s['criteria'])}/{len(s['criteria'])} เกณฑ์ผ่าน "
          f"| เขียน {out} และ {out.with_suffix('.json').name}")
    for c in s["criteria"]:
        print(("PASS " if c["pass"] else "FAIL ") + f"{c['ac']} {c['name']}: {c['got']}/{c['total']} (เกณฑ์ {c['need']})")
    return 0 if s["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
