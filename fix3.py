import json

def src(doc, *kws): return {"doc": doc, "keywords": list(kws)}

PATCH = {
 "q051": {"question": "Quelle équipe a remporté la Coupe du monde de football en 2018 ?",
          "answer": "(absent du corpus)",
          "sources": [src("ABSENT", "Coupe du monde", "2018")]},
}
rows = [json.loads(l) for l in open("eval_draft.jsonl", encoding="utf-8")]
n = 0
for r in rows:
    if r["id"] in PATCH:
        r.update(PATCH[r["id"]]); n += 1
with open("eval_draft.jsonl", "w", encoding="utf-8") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"{n} questions patched")