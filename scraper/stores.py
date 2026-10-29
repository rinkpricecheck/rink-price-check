"""One scraper per store platform. Each returns a list of item dicts:
   {store, name, price, was, url, cond, size, cat?, sub?, level?}
Prices are USD unless noted. Only items listed as purchasable are returned."""
import json, re, time, random, logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("scrape")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0.0.0 Safari/537.36")


class Http:
    def __init__(self, delay=0.6):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                               "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"})
        self.delay = delay
        self.fails = 0

    def get(self, url, as_json=False, tries=3):
        for i in range(tries):
            time.sleep(self.delay + random.random() * self.delay)
            try:
                r = self.s.get(url, timeout=40)
                if r.status_code == 200:
                    return r.json() if as_json else r.text
                if r.status_code in (403, 429, 503):
                    time.sleep(5 * (i + 1))
                if r.status_code == 404:
                    return None
            except Exception as e:  # network blip
                log.debug("get %s: %s", url, e)
                time.sleep(3 * (i + 1))
        self.fails += 1
        log.warning("failed: %s", url)
        return None


def money(s):
    if s is None:
        return None
    m = re.search(r"[\d,]+(?:\.\d+)?", str(s))
    return float(m.group(0).replace(",", "")) if m else None


def soup(h):
    return BeautifulSoup(h or "", "lxml")


# ---------------------------------------------------------------- Pure Hockey / Pure Goalie
PH_CATS = ["/c/hockey-sticks-composite", "/c/hockey-sticks-wood", "/c/ice-hockey-skates", "/c/inline-hockey-skates",
           "/c/recreational-hockey-skates", "/c/hockey-skate-runners-steel-replacement-blades",
           "/c/hockey-protective-helmets", "/c/hockey-protective-facemasks-shields", "/c/hockey-protective-gloves",
           "/c/hockey-protective-elbow-pads", "/c/hockey-protective-shin-guards",
           "/c/hockey-protective-shoulder-pads", "/c/hockey-protective-pants-girdles", "/c/hockey-protective-cups",
           "/c/hockey-bags", "/c/hockey-accessories-tape", "/c/skate-guards-soakers-blade-covers",
           "/c/hockey-clearance"]
PG_CATS = ["/c/goalie-leg-pads", "/c/goalie-catch-gloves", "/c/goalie-blockers", "/c/goalie-masks",
           "/c/goalie-chest-arms", "/c/goalie-pants", "/c/goalie-skates", "/c/goalie-sticks", "/c/goalie-bags",
           "/c/goalie-accessories-knee-guards", "/c/goalie-accessories-neck-protectors",
           "/c/goalie-accessories-jock-jills", "/c/goalie-equipment-sale"]


def pure(store, base, cats, goalie=False):
    http, out, seen = Http(), [], set()
    for c in cats:
        for pg in range(1, 80):
            d = soup(http.get(f"{base}{c}?pg={pg}"))
            items = d.select("div.items div.item[data-base-pdp-url]")
            new = 0
            for it in items:
                url = it["data-base-pdp-url"]
                if url in seen:
                    continue
                seen.add(url); new += 1
                a = it.select_one(".name a")
                name = (a.get_text(" ", strip=True) if a else (it.select_one("img") or {}).get("alt", "")).strip()
                pe = it.select_one(".price")
                if not name or not pe:
                    continue
                price = money((pe.select_one(".price-is") or pe).get_text())
                was = money(pe.select_one(".price-was").get_text()) if pe.select_one(".price-was") else None
                if not price:
                    continue
                rec = dict(store=store, name=name, price=price, was=was, url=url, cond="New", size="")
                if goalie and "goalie" not in name.lower():
                    rec["cat"] = "Goalie"
                out.append(rec)
            if not items or not new:
                break
    return out


def pure_sizes(http, url):
    """In-stock sizes from a Pure Hockey product page."""
    h = http.get(url)
    if not h:
        return None
    m = re.search(r"Product\.mtxArr\s*=\s*(\[.*?\]);", h, re.S)
    stock = {}
    if m:
        try:
            for x in json.loads(m.group(1)):
                stock[str(x["mtxId"])] = x.get("availInv", 0) or 0
        except Exception:
            pass
    tp = re.search(r'Product\.attrTpArr\s*=\s*(\[.*?\]);', h, re.S)
    size_id = None
    if tp:
        try:
            size_id = next((str(a["Id"]) for a in json.loads(tp.group(1)) if a["Desc"].lower() == "size"), None)
        except Exception:
            pass
    out = []
    for li in soup(h).select("li[data-tp-id][data-mtx-ids]"):
        if size_id and li["data-tp-id"] != size_id:
            continue
        ids = li["data-mtx-ids"].split(",")
        if any(stock.get(i, 0) > 0 for i in ids):
            out.append(li.get_text(strip=True))
    return out


# ---------------------------------------------------------------- Magento (HockeyMonkey, Goalie Monkey, Great Skate)
HM_CATS = ["/ice-hockey/skates.html", "/ice-hockey/sticks.html", "/ice-hockey/helmets.html", "/ice-hockey/pads.html",
           "/ice-hockey/hockey-bags.html", "/roller-hockey.html", "/clearance.html", "/accessories.html"]
GM_CATS = ["/equipment/leg-pads.html", "/equipment/gloves.html", "/equipment/blockers.html", "/equipment/skates.html",
           "/equipment/sticks.html", "/equipment/masks.html", "/equipment/chest-arm.html", "/equipment/pants.html",
           "/clearance.html", "/accessories.html"]
GS_CATS = ["/default/skates.html", "/default/sticks.html", "/default/helmets.html", "/default/protective.html",
           "/default/goalie.html", "/default/accessories.html", "/default/street-roller.html",
           "/default/sale-items.html", "/default/outlet-shop.html"]


def magento(store, base, cats, goalie_cats=()):
    http, out, seen = Http(), [], set()
    for c in cats:
        for p in range(1, 60):
            d = soup(http.get(f"{base}{c}?p={p}"))
            items = d.select("li.product-item")
            new = 0
            for li in items:
                a = li.select_one("a.product-item-link[href]") or li.select_one("a.product-item-photo[href]")
                if not a:
                    continue
                url = urljoin(base, a["href"]).split("?")[0]
                if url in seen:
                    continue
                seen.add(url); new += 1
                if li.select_one(".stock.unavailable, .out-of-stock"):
                    continue
                prices = {}
                for pe in li.select("[data-price-amount]"):
                    prices.setdefault(pe.get("data-price-type", ""), float(pe["data-price-amount"]))
                price = prices.get("finalPrice") or prices.get("minPrice") or (min(prices.values()) if prices else None)
                was = max([v for k, v in prices.items() if k in ("oldPrice", "comparePrice", "maxPrice")] or [0]) or None
                if not price:
                    continue
                name = a.get_text(" ", strip=True)
                rec = dict(store=store, name=name, price=price, was=was if was and was > price else None,
                           url=url, cond="New", size="")
                if c in goalie_cats and "goalie" not in name.lower():
                    rec["cat"] = "Goalie"
                out.append(rec)
            if not items or not new:
                break
    return out


def _grab_json(h, key):
    i = h.find(key)
    if i < 0:
        return None
    s = h.find("{", i)
    dep, k = 0, s
    while k < len(h):
        ch = h[k]
        if ch == "{":
            dep += 1
        elif ch == "}":
            dep -= 1
            if not dep:
                return h[s:k + 1]
        elif ch == '"':
            k += 1
            while k < len(h) and h[k] != '"':
                if h[k] == "\\":
                    k += 1
                k += 1
        k += 1
    return None


def magento_sizes(http, url):
    h = http.get(url)
    if not h:
        return None
    raw = _grab_json(h, '"attributes":')
    if not raw:
        return []
    try:
        at = json.loads(raw)
    except Exception:
        return []
    out = []
    for a in at.values():
        if not re.search("size", f"{a.get('code','')} {a.get('label','')}", re.I):
            continue
        for o in a.get("options", []):
            if o.get("products"):
                out.append(o.get("label", ""))
    return out


# ---------------------------------------------------------------- Ice Warehouse
IW_SKIP = re.compile(r"jersey|sock|apparel|hats|beanie|lifestyle|warm-ups|referee|figure|fan_zone|custom|sublimated|"
                     r"^(black|white|grey|blue|red|orange|gold|green|purple|pink)/|solid_color|multi-color|nhl_team|"
                     r"reversible|k1_|water_bottle|injury|coaching|books|mini_knee|base_layer|catpage-$", re.I)


def icewarehouse():
    base = "https://www.icewarehouse.com"
    http, out, seen = Http(delay=1.2), [], set()
    home = soup(http.get(base + "/"))
    cats = []
    for a in home.select('a[href*="catpage-"]'):
        h = a["href"].replace(base, "")
        if h not in cats and not IW_SKIP.search(h.strip("/")):
            cats.append(h)
    for c in cats:
        d = soup(http.get(urljoin(base, c)))
        for a in d.select("a.cattable-wrap-cell-info"):
            url = urljoin(base, a["href"]).split("?")[0]
            if url in seen:
                continue
            seen.add(url)
            nm = a.select_one(".cattable-wrap-cell-info-name")
            sb = a.select_one(".cattable-wrap-cell-info-sub")
            name = " ".join(x.get_text(" ", strip=True) for x in (nm, sb) if x)
            pe = a.select_one(".cattable-wrap-cell-info-price")
            if not name or not pe:
                continue
            span = pe.find("span")
            price = money(span.get_text() if span else pe.get_text())
            was = None
            lp = pe.select_one("[data-list-prices]")
            if lp:
                try:
                    vals = [money(x) for x in json.loads(lp["data-list-prices"])]
                    was = max(v for v in vals if v) if vals else None
                except Exception:
                    pass
            if not price:
                continue
            out.append(dict(store="Ice Warehouse", name=name, price=price, was=was if was and was > price else None,
                            url=url, cond="New", size=""))
    return out


def iw_sizes(http, url):
    h = http.get(url)
    if not h:
        return None
    m = re.search(r'data-gtm_detail_styles="([^"]*)"', h)
    out = []
    if m:
        for s in m.group(1).split(","):
            for part in (p.strip() for p in s.split("/")):
                if re.fullmatch(r"(Y\s*)?\d{1,2}(\.\d)?", part):
                    out.append(part.replace(" ", ""))
                    break
    return out


# ---------------------------------------------------------------- Shopify
def shopify(store, base, keep_types=None, drop_types=(), prefix=""):
    http, out = Http(delay=0.8), []
    for page in range(1, 120):
        j = http.get(f"{base}{prefix}/products.json?limit=250&page={page}", as_json=True)
        ps = (j or {}).get("products") or []
        for p in ps:
            t = p.get("product_type") or ""
            if t in drop_types or (keep_types is not None and t not in keep_types):
                continue
            avail = [v for v in p.get("variants", []) if v.get("available")]
            if not avail:
                continue
            v0 = min(avail, key=lambda v: float(v["price"]))
            price = float(v0["price"])
            was = float(v0["compare_at_price"]) if v0.get("compare_at_price") else None
            sizes = []
            for v in avail:
                tt = v.get("title") or ""
                if tt and tt != "Default Title" and tt not in sizes:
                    sizes.append(tt)
            name = p["title"]
            tags = [x.lower() for x in (p.get("tags") or [])]
            if "used" in tags or re.search(r"\bused\b", name, re.I):
                cond = "Used"
            elif "refurbished" in t.lower() or "refurbished" in tags or re.search(r"refurb", name, re.I):
                cond = "Refurbished"
            elif "pro_stock" in tags or "pro stock" in t.lower():
                cond = "Pro stock"
            else:
                cond = "New"
            rec = dict(store=store, name=name, price=price, was=was if was and was > price else None,
                       url=f"{base}{prefix}/products/{p['handle']}", cond=cond, size=", ".join(sizes)[:300], type=t)
            if t.lower().startswith("goalie") and "goalie" not in name.lower():
                rec["cat"] = "Goalie"
            out.append(rec)
        if len(ps) < 250:
            break
    return out


SE_KEEP = {"Protective", "Sticks", "Skates", "Hockey Accessories", "Helmets & Protective Gear", "Bags", ""}
DH_DROP = {"Apparel", "Athletic Socks", "Compression Shirts", "Custom Jerseys", "Figure Bags/Frames/Inserts",
           "Figure Skates/Blades", "Floorball", "Footwear", "Gift Card", "Hats", "Hockey Socks", "Hoodies", "Jerseys",
           "OPTIONS_HIDDEN_PRODUCT", "Referee Accessories", "Service", "Shirts", "Souvenirs / Novelty",
           "Team Orders", "Warmup Jackets", "Warmup Pants", "Mini Sticks", "Water Bottles", "General", ""}
HSM_DROP = {"Hockey Jerseys", "Hockey Socks", "Apparel", "Custom Apparel", "Custom Hockey Jerseys", "Custom Bags",
            "Pro Shop Service", "Jocks & Base Layers"}


# ---------------------------------------------------------------- BigCommerce: Play It Again Sports
PIA_CATS = {  # path -> (category hint, sub hint)
    "/skates/ice-hockey-skates/": ("Skates", None), "/skates/goalie-skates/": ("Goalie", "Goalie skates"),
    "/street-hockey/roller-hockey-skates/": ("Skates", None),
    "/sticks/senior-one-piece-sticks/": ("Sticks", None), "/sticks/intermediate-one-piece-sticks/": ("Sticks", None),
    "/sticks/junior-one-piece-sticks/": ("Sticks", None), "/sticks/youth-one-piece-sticks/": ("Sticks", None),
    "/hockey/hockey-pants/": ("Pants", None), "/hockey/hockey-shoulder-pads/": ("Shoulder pads", None),
    "/hockey/hockey-shin-guards/": ("Shin guards", None), "/hockey/hockey-elbow-pads/": ("Elbow pads", None),
    "/hockey/hockey-gloves/": ("Gloves", None), "/hockey/hockey-helmets/": ("Helmets", None),
    "/hockey/hockey-equipment-bags/": ("Bags", None), "/hockey/hockey-accessories/": ("Accessories", None),
    "/hockey/hockey-jocks/": ("Accessories", None), "/hockey/hockey-neck-guards/": ("Accessories", None),
    "/hockey/hockey-training-aids/": ("Accessories", None), "/hockey/hockey-protective-sets/": ("Accessories", None),
    "/goalie/goalie-leg-pads/": ("Goalie", "Leg pads"), "/goalie/goalie-catchers/": ("Goalie", "Catch glove"),
    "/goalie/goalie-blockers/": ("Goalie", "Blocker"), "/goalie/goalie-body-armour/": ("Goalie", "Chest & arm"),
    "/goalie/goalie-pants/": ("Goalie", "Goalie pants"), "/goalie/goalie-sticks/": ("Goalie", "Goalie stick"),
    "/goalie/goalie-helmets-and-masks/": ("Goalie", "Mask"), "/goalie/goalie-accessories/": ("Goalie", "Other goalie"),
    "/goalie/goalie-jocks-and-cups/": ("Goalie", "Other goalie"),
    "/goalie/goalie-neck-and-throat-guards/": ("Goalie", "Other goalie"),
}
SIZE_TAIL = re.compile(r'\s((?:\d{1,2}(?:\.\d{1,2})?"?)|XXS|XS|SM|MD|LG|XL|XXL|XXXL|S|M|L|OSFA)$')


def playitagain():
    base = "https://playitagainsports.com"
    http, out, seen = Http(delay=0.7), [], set()
    for path, (c, sb) in PIA_CATS.items():
        for page in range(1, 101):  # 100 pages x 100 = BigCommerce's 10,000-result cap
            d = soup(http.get(f"{base}{path}?limit=100&page={page}"))
            cards = d.select("article.card")
            new = 0
            for card in cards:
                a = card.select_one("a[href]")
                if not a:
                    continue
                url = a["href"]
                if url in seen:
                    continue
                seen.add(url); new += 1
                name = re.sub(r"\s+\d{4,6}-[A-Z0-9][A-Z0-9-]*\s*$", "", card.get("data-name", "")).strip()
                name = re.sub(r"^New\s+", "", name)  # every Play It Again listing is shown as Used
                price = money(card.get("data-product-price"))
                if not name or not price:
                    continue
                loc = card.get("data-product-brand", "").strip()  # "MN - Maple Grove"
                m = re.match(r"([A-Z]{2})\s*-\s*(.+)", loc)
                loc = f"{m.group(2).strip()}, {m.group(1)}" if m else loc
                sm = SIZE_TAIL.search(name)
                size = sm.group(1) if sm else ""
                rec = dict(store="Play It Again Sports", name=name, price=price, was=None, url=url, cond="Used",
                           size=" · ".join(x for x in (size, loc) if x), cat=c)
                if sb:
                    rec["sub"] = sb
                out.append(rec)
            if not cards or not new:
                break
    return out


# ---------------------------------------------------------------- BigCommerce: Pro Stock Hockey
PSH_CATS = {"/player-sticks/": ("Sticks", "Pro stock"), "/goalie-sticks/": ("Goalie", "Pro stock"),
            "/clearance-sticks/": ("Sticks", "Pro stock"), "/used-hockey-sticks/": ("Sticks", "Used"),
            "/kids-hockey-sticks/": ("Sticks", "Pro stock"), "/gloves/": ("Gloves", "Pro stock"),
            "/used-hockey-gloves/": ("Gloves", "Used"), "/kids-hockey-gloves/": ("Gloves", "Pro stock"),
            "/pants/": ("Pants", "Pro stock"), "/helmets/": ("Helmets", "Pro stock"),
            "/pant-shells-girdles/": ("Pants", "Pro stock"), "/elbow-pads/": ("Elbow pads", "Pro stock"),
            "/shin-guards/": ("Shin guards", "Pro stock"), "/shoulder-pads/": ("Shoulder pads", "Pro stock"),
            "/player-skates/": ("Skates", "Pro stock"), "/goalie-skates/": ("Goalie", "Pro stock"),
            "/used-hockey-skates/": ("Skates", "Used"), "/goalie-blockers/": ("Goalie", "Pro stock"),
            "/goalie-chest-protectors/": ("Goalie", "Pro stock"), "/hockey-goalie-gloves/": ("Goalie", "Pro stock"),
            "/goalie-masks/": ("Goalie", "Pro stock"), "/goalie-pads/": ("Goalie", "Pro stock"),
            "/hockey-goalie-pants/": ("Goalie", "Pro stock"), "/equipment-bags/": ("Bags", "Pro stock"),
            "/visors/": ("Helmets", "Pro stock")}
PSH_SUB = {"/goalie-sticks/": "Goalie stick", "/goalie-skates/": "Goalie skates", "/goalie-blockers/": "Blocker",
           "/goalie-chest-protectors/": "Chest & arm", "/hockey-goalie-gloves/": "Catch glove",
           "/goalie-masks/": "Mask", "/goalie-pads/": "Leg pads", "/hockey-goalie-pants/": "Goalie pants"}


def prostock():
    base = "https://www.prostockhockey.com"
    http, out, seen = Http(), [], set()
    for path, (c, cond) in PSH_CATS.items():
        for page in range(1, 60):
            d = soup(http.get(f"{base}{path}?limit=100&page={page}"))
            cards = d.select("article.card")
            new = 0
            for card in cards:
                a = card.select_one("a[href]")
                if not a:
                    continue
                url = a["href"]
                if url in seen:
                    continue
                seen.add(url); new += 1
                name = card.get("data-name", "").strip()
                price = money(card.get("data-product-price"))
                if not name or not price:
                    continue
                rrp = card.select_one(".price--rrp, .price--non-sale")
                was = money(rrp.get_text()) if rrp and rrp.get_text(strip=True) else None
                rec = dict(store="Pro Stock Hockey", name=name, price=price, was=was if was and was > price else None,
                           url=url, cond=cond, size=(re.match(r"Size ([\d.]+)", name) or [None, ""])[1], cat=c)
                if path in PSH_SUB:
                    rec["sub"] = PSH_SUB[path]
                if "kids" in path:
                    rec["level"] = "Junior"
                out.append(rec)
            if not cards or not new:
                break
    return out


# ---------------------------------------------------------------- registry
STORES = {
    "Pure Hockey": lambda: pure("Pure Hockey", "https://www.purehockey.com", PH_CATS),
    "Pure Goalie": lambda: pure("Pure Goalie", "https://goalie.purehockey.com", PG_CATS, goalie=True),
    "HockeyMonkey": lambda: magento("HockeyMonkey", "https://www.hockeymonkey.com", HM_CATS),
    "Goalie Monkey": lambda: magento("Goalie Monkey", "https://www.goaliemonkey.com", GM_CATS,
                                     goalie_cats=set(GM_CATS[:8])),
    "Great Skate": lambda: magento("Great Skate", "https://greatskate.com", GS_CATS,
                                   goalie_cats={"/default/goalie.html"}),
    "Ice Warehouse": icewarehouse,
    "Discount Hockey": lambda: shopify("Discount Hockey", "https://discounthockey.com", drop_types=DH_DROP),
    "Sports Excellence": lambda: shopify("Sports Excellence", "https://sportsexcellence.com", keep_types=SE_KEEP,
                                         prefix="/en-us"),
    "HockeyTron": lambda: shopify("HockeyTron", "https://hockeytron.com"),
    "HockeyStickMan": lambda: shopify("HockeyStickMan", "https://www.hockeystickman.com", drop_types=HSM_DROP),
    "Pro Stock Hockey": prostock,
    "Play It Again Sports": playitagain,
}
SIZE_FETCHERS = {"Pure Hockey": pure_sizes, "Pure Goalie": pure_sizes, "HockeyMonkey": magento_sizes,
                 "Goalie Monkey": magento_sizes, "Great Skate": magento_sizes, "Ice Warehouse": iw_sizes}
