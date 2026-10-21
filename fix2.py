import json

def src(doc, *kws): return {"doc": doc, "keywords": list(kws)}

PATCH = {
 "q026": {"sources": [src("ABSENT", "Golden Lion", "Joker")]},
 "q051": {"question": "Quel est le tarif d'un billet pour le Festival de Cannes ?",
          "sources": [src("ABSENT", "Cannes", "tarif|prix d'entrée|prix du billet")]},
 "q066": {"type": "single",
          "question": "Citez un film qui a reçu à la fois la Palme d'or et l'Oscar du meilleur film.",
          "answer": "Parasite (2019).",
          "sources": [src("Parasite (film, 2019)", "Palme d'or", "Oscar du meilleur film")]},
}
rows = [json.loads(l) for l in open("eval_draft.jsonl", encoding="utf-8")]
n = 0
for r in rows:
    if r["id"] in PATCH:
        r.update(PATCH[r["id"]]); n += 1
with open("eval_draft.jsonl", "w", encoding="utf-8") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"{n} questions patched")