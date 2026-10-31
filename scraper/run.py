"""Refresh every store, classify, and write the site's data files.

usage: python scraper/run.py OUT_DIR [--prev URL_OR_DIR] [--only "Store A,Store B"]

A store that fails, or comes back with under half of its previous item count,
keeps its previous listings so one blocked site never empties the page."""
import argparse, datetime, hashlib, json, logging, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
import classify as C
import stores as S

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run")
FILES = ("deals.json", "used-pias.json")
USED_STORE = "Play It Again Sports"
CA_PROV = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}


def in_canada(d):
    """Play It Again Sports location is the last part of the size field ("9 · Whitby, ON") or the URL slug."""
    m = re.search(r",\s*([A-Z]{2})\s*$", (d.get("size") or "").split(" · ")[-1])
    if m:
        return m.group(1) in CA_PROV
    m = re.search(r"/locations/([a-z0-9-]+)/", d["url"])
    return bool(m) and any(t.upper() in CA_PROV for t in m.group(1).split("-")[1:])


# ---------------------------------------------------------------- previous data
def load_prev(src):
    import requests
    packs = []
    for f in FILES:
        try:
            if src.startswith("http"):
                r = requests.get(src.rstrip("/") + "/" + f, timeout=60)
                r.raise_for_status(); packs.append(r.json())
            else:
                packs.append(json.load(open(os.path.join(src, f))))
        except Exception as e:
            log.warning("previous %s not loaded from %s: %s", f, src, e)
    items = []
    for p in packs:
        for r in p["r"]:
            s = r[5]; suf = r[8]
            items.append(dict(name=r[0], brand=p["B"][r[1]], cat=p["C"][r[2]], level=p["L"][r[3]],
                              play="Roller" if r[4] else "Ice", store=p["S"][s], price=r[6], was=r[7] or None,
                              url=suf if re.match(r"https?:", suf) else p["P"][s] + suf, cond=p["K"][r[9]],
                              size=r[10], line=p["M"][r[11]], sub=p["U"][r[12]], id=r[13], _done=True))
    return items


# ---------------------------------------------------------------- skate sizes
def is_skate(d):
    n = d["name"].lower()
    return (d.get("cat") == "Skates" or (d.get("cat") in (None, "Goalie") and "skate" in n)) and \
        not re.search(r"guard|soaker|lace|runner|holder|tongue|insole|\bbags?\b|sharpen|tile|fender|wheel|cover|carrying|tightener|tape|towel|insert|footbed", n)


def is_pad(d):
    if d.get("sub"):
        return d["sub"] == "Leg pads"
    return d.get("cat") in (None, "Goalie") and "goalie" in d["name"].lower() and \
        C.sub(d["name"], "Goalie", "Ice") == "Leg pads"


def fmt_pad_sizes(tokens):
    out = []
    for t in tokens:
        t = re.sub(r"\s*in\.?\s*$", '"', t.strip()).replace("''", '"')
        if t and t not in out:
            out.append(t)
    return ", ".join(out)


def norm_size(tok):
    t = tok.strip()
    y = bool(re.search(r"(^|\s)(y|yth|youth)\b|^y\s*\d|\d\s*y\b", t, re.I))
    m = re.search(r"(\d{1,2}(?:\.\d{1,2})?)", t)
    if not m:
        return None
    n = round(float(m.group(1)) * 2) / 2
    if n < 1 or n > 15:
        return None
    s = str(int(n)) if n == int(n) else str(n)
    return ("Y" + s) if y else s


def fmt_sizes(tokens, lvl):
    vals = {v for v in (norm_size(t) for t in tokens) if v}
    if lvl == "Youth":
        vals = {("Y" + v) if (not v.startswith("Y") and float(v) >= 6) else v for v in vals}
    key = lambda s: (0 if s.startswith("Y") else 1, float(s.lstrip("Y")))
    return ", ".join(sorted(vals, key=key))


def add_sizes(store, items):
    f = S.SIZE_FETCHERS.get(store)
    if not f:
        return
    http = S.Http(delay=1.5 if store == "Ice Warehouse" else 0.5)  # Ice Warehouse blocks fast requests
    todo = ([d for d in items if is_skate(d)] + [d for d in items if is_pad(d)])[:600]
    got = 0
    for d in todo:
        try:
            sz = f(http, d["url"])
        except Exception as e:
            log.debug("sizes %s: %s", d["url"], e); sz = None
        if sz:
            d["size"] = fmt_pad_sizes(sz) if is_pad(d) else fmt_sizes(sz, C.level(d["name"])); got += 1
    log.info("%s: sizes for %d of %d skates and goalie pads", store, got, len(todo))


# ---------------------------------------------------------------- classify fresh items
def finish(d):
    n = d["name"]
    clean = re.sub(r"\s*\((Used|New)\)\s*$", "", re.sub(r"^Used\s+", "", n)).strip()
    play = "Roller" if re.search(r"roller|inline", n, re.I) else "Ice"
    cat = d.get("cat") or C.cat(n)
    if not d.get("cat") and cat == "Accessories" and d.get("type"):
        cat = C.cat(d["type"])  # e.g. a stick titled only "True Catalyst Nitro"
    lvl = d.get("level") or C.level(n)
    key = d["url"].split("?color=")[0].rstrip("?")
    out = dict(name=clean, brand=C.brand(clean), cat=cat, level=lvl, play=play, store=d["store"], price=d["price"],
               was=d.get("was") if d.get("was") and d["was"] > d["price"] else None, url=d["url"], cond=d["cond"],
               size=d.get("size") or "", line=C.line(clean),
               id=hashlib.md5((key + n + n).encode()).hexdigest()[:10])
    out["sub"] = d.get("sub") or C.sub(n, cat, play)
    if out["sub"] == "Leg pads" and not out["level"]:  # pro-stock pads rarely say Senior
        m = re.search(r"(\d{2}(?:\.\d)?)\s*(?:\"|''|in\b|\+)", out["size"] + " " + clean)
        if m and float(m.group(1)) >= 32:
            out["level"] = "Senior"
    if out["store"] != USED_STORE and out["size"] and is_skate(out):
        s = fmt_sizes(re.split(r",\s*", out["size"]), lvl)
        if s:
            out["size"] = s
    return out


# ---------------------------------------------------------------- pack (same format the page reads)
def pack(items, stamp):
    keys = "SBCLKMU"
    dicts = {k: [] for k in keys}; idx = {k: {} for k in keys}; P = []

    def ix(k, v):
        v = v or ""
        if v not in idx[k]:
            idx[k][v] = len(dicts[k]); dicts[k].append(v)
        return idx[k][v]
    rows = []
    for d in items:
        m = re.match(r"(https?://[^/]+)(.*)", d["url"]); host, suf = m.group(1), m.group(2)
        s = ix("S", d["store"])
        while len(P) <= s:
            P.append(None)
        if P[s] is None:
            P[s] = host
        if P[s] != host:
            suf = d["url"]
        rows.append([d["name"], ix("B", d["brand"]), ix("C", d["cat"]), ix("L", d["level"]),
                     1 if d["play"] == "Roller" else 0, s, round(d["price"], 2), round(d.get("was") or 0, 2), suf,
                     ix("K", d["cond"]), d.get("size", ""), ix("M", d.get("line", "")), ix("U", d.get("sub", "")),
                     d["id"]])
    out = {"u": stamp}; out.update(dicts); out["P"] = P; out["r"] = rows
    return out


def scrape(name):
    t = time.time()
    items = S.STORES[name]()
    add_sizes(name, items)
    log.info("%s: %d items in %.0fs", name, len(items), time.time() - t)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--prev", default=os.path.join(os.path.dirname(__file__), "..", "seed"))
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    prev = load_prev(a.prev)
    if not prev and a.prev.startswith("http"):
        prev = load_prev(os.path.join(os.path.dirname(__file__), "..", "seed"))
    by_store = {}
    for d in prev:
        by_store.setdefault(d["store"], []).append(d)
    names = [x.strip() for x in a.only.split(",") if x.strip()] or list(S.STORES)
    status = {}
    fresh = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(scrape, n): n for n in names}
        for f in as_completed(futs):
            n = futs[f]
            try:
                items = [x for x in f.result() if not C.is_junk(x["name"])]
            except Exception as e:
                log.exception("%s failed", n); items = []
            old = len(by_store.get(n, []))
            if len(items) >= max(10, old * 0.5):
                fresh[n] = items; status[n] = {"fresh": True, "count": len(items), "previous": old}
            else:
                status[n] = {"fresh": False, "count": old, "got": len(items),
                             "note": "kept previous listings (store blocked or returned too few items)"}
    # a skate whose size lookup failed this time keeps the sizes from the last run
    old_size = {}
    for d in load_prev(os.path.join(os.path.dirname(__file__), "..", "seed")) + prev:  # newer runs override starter data
        if d.get("size") and (is_skate(d) or is_pad(d)):
            old_size[d["url"]] = d["size"]
    for items in fresh.values():
        for d in items:
            if not d.get("size") and d["url"] in old_size and (is_skate(d) or is_pad(d)):
                d["size"] = old_size[d["url"]]
    for n in list(fresh):
        if n == USED_STORE:
            fresh[n] = [d for d in fresh[n] if not in_canada(d)]  # US stores only, so every price is in US dollars
    if USED_STORE in by_store:
        by_store[USED_STORE] = [d for d in by_store[USED_STORE] if not in_canada(d)]
    out, seen = [], set()
    for n, items in fresh.items():
        for d in items:
            r = finish(d)
            if n == USED_STORE:
                r["cond"] = "Used"
            k = (r["url"].split("?color=")[0].rstrip("?"), r["name"]) if "collections/" in r["url"] \
                else r["url"].split("?color=")[0].rstrip("?")
            if k in seen:
                continue
            seen.add(k); out.append(r)
    for n, items in by_store.items():
        if n in fresh:
            continue
        status.setdefault(n, {"fresh": False, "count": len(items), "note": "carried over (no scraper)"})
        for d in items:
            d.pop("_done", None); out.append(d)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(a.out, exist_ok=True)
    main_items = [d for d in out if d["store"] != USED_STORE]
    used = [d for d in out if d["store"] == USED_STORE]
    for f, items in zip(FILES, (main_items, used)):
        s = json.dumps(pack(items, stamp), separators=(",", ":"), ensure_ascii=False)
        open(os.path.join(a.out, f), "w", encoding="utf-8").write(s)
        log.info("wrote %s: %d items, %d KB", f, len(items), len(s) // 1024)
    json.dump({"updatedAt": stamp, "stores": status}, open(os.path.join(a.out, "status.json"), "w"), indent=1)
    for n, s in sorted(status.items()):
        log.info("%-22s %s", n, s)


if __name__ == "__main__":
    main()
