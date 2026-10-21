"""Patches eval_draft.jsonl for the 15 flagged questions (matched by id). Safe to run twice.
Usage: python fix_draft.py   (then: python build_corpus.py  and  python attach_passages.py)"""
import json

def src(doc, *kws): return {"doc": doc, "keywords": list(kws)}
EEAAO, ANORA, PAR = "Everything Everywhere All at Once", "Anora", "Parasite (film, 2019)"

PATCH = {
 "q001": {"sources": [src("ABSENT", "The Matrix", "soundtrack|score|composer|composed")]},
 "q002": {"sources": [src("ABSENT", "Ours d'or", "1990")]},
 "q026": {"sources": [src("ABSENT", "Golden Lion", "2019")]},
 "q029": {"question": "What is the population of the city of Cannes?",
          "sources": [src("ABSENT", "Cannes", "population|inhabitants")]},
 "q038": {"sources": [src("Parasite (2019 film)", "Bong Joon")]},
 "q050": {"sources": [src("Parasite (2019 film)", "Bong Joon")]},
 "q051": {"sources": [src("ABSENT", "Intouchables", "spectateurs|entrées")]},
 "q052": {"sources": [src("ABSENT", "Carthage", "phone number|telephone")]},
 "q066": {"sources": [src(PAR, "Palme d'or", "Oscar du meilleur film"),
                      src(ANORA, "Palme d'or"), src(ANORA, "Oscar du meilleur film|meilleur film")]},
 "q078": {"sources": [src("ABSENT", "Avatar", "budget")]},
 "q087": {"sources": [src(EEAAO, "Michelle Yeoh"), src(EEAAO, "Best Actress")]},
 "q090": {"sources": [src("ABSENT", "The Dark Knight", "durée|minutes")]},
 "q098": {"sources": [src("Shoplifters (film)", "Palme d'Or", "2018")]},
 "q100": {"sources": [src("ABSENT", "Inception", "budget")]},
 "q104": {"sources": [src("ABSENT", "Tanit d'Or", "2040")]},
}
rows = [json.loads(l) for l in open("eval_draft.jsonl", encoding="utf-8")]
n = 0
for r in rows:
    if r["id"] in PATCH:
        r.update(PATCH[r["id"]]); n += 1
with open("eval_draft.jsonl", "w", encoding="utf-8") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"{n} questions patched")