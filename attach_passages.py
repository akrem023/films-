"""Step 2: attach the exact source passage to every question and verify it.
Usage:  python attach_passages.py
Needs:  eval_draft.jsonl, data/corpus.jsonl, data/title_map.json
Output: data/eval.jsonl (final dataset) and data/review.txt (items to fix by hand)

For each source, the script looks for a paragraph (or two adjacent ones) that contains ALL the
evidence keywords. "a|b" means "a or b". If nothing matches, the item is flagged
needs_review: either the fact in my draft is wrong, or the keyword is too strict. Check it by hand.
For unanswerable questions, it checks that the keyword really is absent from the corpus.
"""
import json, re, unicodedata
from collections import defaultdict

def norm(s):
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).lower()

def has(text, kw):
    return any(norm(alt.strip()) in text for alt in kw.split("|"))

corpus = {}
for line in open("data/corpus.jsonl", encoding="utf-8"):
    d = json.loads(line)
    corpus[(d["lang"], d["title"])] = d
tmap = json.load(open("data/title_map.json", encoding="utf-8"))

def paragraphs(text):
    sec, out = "Introduction", []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        m = re.match(r"^=+\s*(.*?)\s*=+$", ln)
        if m:
            sec = m.group(1); continue
        out.append((sec, ln))
    return out

paras = {k: paragraphs(v["text"]) for k, v in corpus.items()}
all_text = {lang: norm(" ".join(v["text"] for (l, _), v in corpus.items() if l == lang)) for lang in ("en", "fr")}

def find(lang, doc, kws):
    title = tmap.get(f"{lang}|{doc}")
    if not title or (lang, title) not in corpus:
        return None, f"article not found: {doc}"
    P = paras[(lang, title)]
    for i, (sec, p) in enumerate(P):
        if all(has(norm(p), k) for k in kws):
            return {"doc": title, "url": corpus[(lang, title)]["url"], "section": sec, "passage": p[:1500]}, None
    for i in range(len(P) - 1):
        joined = P[i][1] + " " + P[i + 1][1]
        if all(has(norm(joined), k) for k in kws):
            return {"doc": title, "url": corpus[(lang, title)]["url"], "section": P[i][0], "passage": joined[:1500]}, None
    return None, f"keywords {kws} not found together in '{title}'"

rows, review, count_by_type = [], [], defaultdict(int)
for line in open("eval_draft.jsonl", encoding="utf-8"):
    q = json.loads(line)
    problems, srcs = [], []
    if q["answerable"]:
        for s in q["sources"]:
            hit, err = find(q["lang"], s["doc"], s["keywords"])
            if hit: srcs.append(hit)
            else: problems.append(err)
    else:
        # answerable only if ONE paragraph contains ALL the keywords (a mere mention is not an answer)
        for s in q["sources"]:
            for (l, title), P in paras.items():
                if l != q["lang"]:
                    continue
                for sec, p in P:
                    if all(has(norm(p), k) for k in s["keywords"]):
                        problems.append(f"possible answer in '{title}': {p[:220]}...")
                        break
    i = count_by_type[q["type"]]; count_by_type[q["type"]] += 1
    q["split"] = "test" if i % 10 in (2, 5, 8) else "dev"      # ~30% held-out test set, stratified by type
    q["sources"] = srcs
    q["status"] = "needs_review" if problems else "verified"
    if problems:
        review.append(f"{q['id']} [{q['lang']}/{q['type']}] {q['question']}\n    - " + "\n    - ".join(problems))
    rows.append(q)

with open("data/eval.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
open("data/review.txt", "w", encoding="utf-8").write("\n\n".join(review))
ok = sum(r["status"] == "verified" for r in rows)
print(f"{len(rows)} questions | verified: {ok} | needs_review: {len(rows) - ok} (see data/review.txt)")
print("test split:", sum(r['split'] == 'test' for r in rows), "| dev split:", sum(r['split'] == 'dev' for r in rows))