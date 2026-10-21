import json, random, sys
from collections import Counter

def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

def sample(n=20):
    rows = load("data/eval.jsonl")
    random.seed()
    pick = random.sample(rows, min(n, len(rows)))
    out = []
    for r in pick:
        out.append(f"=== {r['id']}  [{r['lang']}/{r['type']}]\nQUESTION: {r['question']}\nANSWER:   {r['answer']}")
        if r["sources"]:
            for s in r["sources"]:
                out.append(f"SOURCE:   {s['doc']} / {s['section']}\nPASSAGE:  {s['passage'][:500]}")
        else:
            out.append("SOURCE:   (none - unanswerable question)")
        out.append("OK? [  ] yes   [  ] wrong answer   [  ] unclear question   [  ] passage does not say it\n")
    open("data/spotcheck.txt", "w", encoding="utf-8").write("\n".join(out))
    print(f"Wrote data/spotcheck.txt with {len(pick)} items. Open it in VS Code or Notepad and review.")

def stats():
    rows = load("data/eval.jsonl")
    print("Total:", len(rows))
    for key in ("type", "lang", "split", "answerable"):
        print(key, dict(Counter(str(r.get(key)) for r in rows)))
    print("source:", dict(Counter(r.get("source", "generated") for r in rows)))
    fr = sum(r["lang"] == "fr" for r in rows) / len(rows)
    un = sum(not r["answerable"] for r in rows) / len(rows)
    print(f"French: {fr:.0%} | unanswerable: {un:.0%} | status not verified: {sum(r['status'] != 'verified' for r in rows)}")

def add():
    rows = load("eval_draft.jsonl")
    nxt = max(int(r["id"][1:]) for r in rows) + 1
    print("Adding a real-user question (Ctrl+C to cancel).")
    lang = input("Language (en/fr): ").strip()
    typ = input("Type (single/multi/vague/time/unanswerable): ").strip()
    q = input("Question exactly as the user asked it: ").strip()
    a = input("Answer (short; for unanswerable type: (not in the corpus)): ").strip()
    sources = []
    if typ != "unanswerable":
        print("Source article(s). Empty title to stop. Keywords = words that must appear together in the passage; use a|b for alternatives.")
        while True:
            doc = input("  Wikipedia article title: ").strip()
            if not doc: break
            kws = [k.strip() for k in input("  Keywords (comma separated): ").split(",") if k.strip()]
            sources.append({"doc": doc, "keywords": kws})
    else:
        kws = [k.strip() for k in input("  Keywords that would appear if it WERE answerable (comma separated): ").split(",") if k.strip()]
        sources.append({"doc": "ABSENT", "keywords": kws})
    rec = {"id": f"q{nxt:03d}", "lang": lang, "type": typ, "question": q, "answer": a,
           "answerable": typ != "unanswerable", "sources": sources, "source": "real_user"}
    with open("eval_draft.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("Added", rec["id"])

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "sample": sample(int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    elif cmd == "stats": stats()
    elif cmd == "add": add()
    else: print("Usage: python dataset_tools.py sample [N] | stats | add")