"""Step 1: download the Wikipedia articles used by the eval set (+ distractor articles).
Usage:  pip install requests && python build_corpus.py
Resumable: downloaded articles are cached in data/cache/, so just re-run after an error.
Output: data/corpus.jsonl, data/title_map.json
Text is CC BY-SA 4.0 (Wikipedia): keep the URL/revision metadata for attribution.
"""
import json, os, re, time, requests

EVAL = "eval_draft.jsonl"
OUT = "data"
CONTACT = "your-email@example.com"   # <-- put YOUR email here (Wikimedia asks for a contact)
UA = {"User-Agent": f"CS496-Librarian/1.0 (student project; {CONTACT})"}
PAUSE = 1.0   # seconds between requests

# Extra articles = distractors, so the corpus is bigger than the questions need.
EXTRA = {
 "en": ["Rain Man","Platoon (film)","Rocky","Annie Hall","Chariots of Fire","Gandhi (film)","Amadeus (film)",
        "Out of Africa (film)","The Last Emperor","Dances with Wolves","The Silence of the Lambs (film)",
        "Unforgiven","Braveheart","The English Patient (film)","Shakespeare in Love","American Beauty (1999 film)",
        "A Beautiful Mind (film)","Chicago (2002 film)","Million Dollar Baby","Crash (2004 film)",
        "Taxi Driver","The Conversation","Viridiana","Blow-Up","The Mission (1986 film)",
        "Sex, Lies, and Videotape","Wild at Heart (film)","Barton Fink","Underground (1995 film)",
        "Secrets & Lies (1996 film)","Taste of Cherry","Rosetta (film)","Elephant (2003 film)",
        "Uncle Boonmee Who Can Recall His Past Lives","The Class (2008 film)","Palme d'Or",
        "Academy Award for Best Picture","Academy Awards","Kaouther Ben Hania","Tahar Cheriaa",
        "Ousmane Sembène","Abdellatif Kechiche","Bong Joon-ho","Hattie McDaniel"],
 "fr": ["Palme d'or","Oscar du meilleur film","Oscars du cinéma","Kaouther Ben Hania","Tahar Cheriaa",
        "Abdellatif Kechiche","Bong Joon-ho","Jane Campion","Quentin Tarantino","Roman Polanski",
        "Les Oscars"," Michael Haneke","Ken Loach","Jacques Audiard","Hirokazu Kore-eda",
        "Le Voleur de bicyclette","Les Quatre Cents Coups","Le Troisième Homme","Underground (film)",
        "Mandabi","Halfaouine, l'enfant des terrasses","Le Bleu du caftan"],
}

def api(lang, **params):
    p = {"format": "json", "formatversion": 2, "action": "query"}
    p.update(params)
    url = f"https://{lang}.wikipedia.org/w/api.php"
    for attempt in range(8):
        r = requests.get(url, params=p, headers=UA, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504):
            wait = int(r.headers.get("Retry-After", 0)) or min(120, 5 * 2 ** attempt)
            print(f"  [{r.status_code}] waiting {wait}s then retrying...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    raise RuntimeError("Wikipedia keeps refusing; wait a few minutes and run the script again")

def fetch(lang, title):
    d = api(lang, titles=title, redirects=1, prop="extracts|info", explaintext=1,
            exsectionformat="wiki", inprop="url")
    page = d["query"]["pages"][0]
    if page.get("missing"):
        s = api(lang, list="search", srsearch=title, srlimit=1)["query"]["search"]
        if not s:
            return None
        d = api(lang, titles=s[0]["title"], redirects=1, prop="extracts|info",
                explaintext=1, exsectionformat="wiki", inprop="url")
        page = d["query"]["pages"][0]
        if page.get("missing"):
            return None
    return {"lang": lang, "requested": title, "title": page["title"], "url": page["fullurl"],
            "revid": page.get("lastrevid"), "license": "CC BY-SA 4.0 (Wikipedia)",
            "text": page.get("extract", "")}

def cache_path(lang, title):
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title)[:80]
    return f"{OUT}/cache/{lang}_{slug}.json"

def main():
    need = {"en": set(EXTRA["en"]), "fr": {t.strip() for t in EXTRA["fr"]}}
    for line in open(EVAL, encoding="utf-8"):
        q = json.loads(line)
        for s in q["sources"]:
            if s["doc"] != "ABSENT":
                need[q["lang"]].add(s["doc"])
    os.makedirs(f"{OUT}/cache", exist_ok=True)
    total = sum(len(v) for v in need.values()); k = 0
    tmap, missing, seen, n = {}, [], set(), 0
    with open(f"{OUT}/corpus.jsonl", "w", encoding="utf-8") as f:
        for lang in ("en", "fr"):
            for t in sorted(need[lang]):
                k += 1
                cp = cache_path(lang, t)
                if os.path.exists(cp):
                    doc = json.load(open(cp, encoding="utf-8"))
                    if doc.get("_missing"):
                        missing.append((lang, t)); continue
                else:
                    print(f"[{k}/{total}] {lang}: {t}")
                    doc = fetch(lang, t)
                    json.dump(doc or {"_missing": True}, open(cp, "w", encoding="utf-8"), ensure_ascii=False)
                    if not doc:
                        missing.append((lang, t)); continue
                tmap[f"{lang}|{t}"] = doc["title"]
                if (lang, doc["title"]) in seen:
                    continue
                seen.add((lang, doc["title"]))
                f.write(json.dumps(doc, ensure_ascii=False) + "\n"); n += 1
                if doc["title"] != t:
                    print(f"  [resolved] {lang}: {t} -> {doc['title']}")
    json.dump(tmap, open(f"{OUT}/title_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{n} articles saved. Missing: {missing}")

if __name__ == "__main__":
    main()