"""Model year for new CCM, True and Vaughn gear.

1. A year the store states (name "(2026)", season code "S26", '22 Model, Goalie Monkey links ending -25.html).
2. Otherwise the year other stores state for the same model (same brand, line and model code).
3. Otherwise the launch year from the table below, marked approximate ("2023~")."""
import collections
import re

BRANDS = ("CCM", "True", "Vaughn")

GEN = re.compile(r"^(?:[a-z]*\d[a-z0-9.]*|pro|plus|select|carbon|lite|nitro|smoke|team|max|maxx|se|premier|vector|"
                 r"unleashed|trigger|asv|as|xf|xr|ft|ftw|px|ax|x|super|origin|recharge|storm)$")
STOP = set("""senior intermediate junior youth sr int jr yth yt goalie hockey ice inline roller skate skates stick sticks glove
gloves helmet helmets combo pant pants girdle shin guard guards elbow shoulder pad pads leg chest arm protector blocker catcher
catch trapper mask mens womens women men kids composite grip wood player custom return stock edition le limited blade blades bag
knee neck jock body armor armour cage facemask visor shell shells""".split())
LINE_WORDS = {"ccm": ["super tacks", "tacks", "jetspeed", "ribcor", "next", "eflex", "axis", "phenom", "ytflex", "vizion"],
              "true": ["catalyst", "hzrdus", "project x"],
              "vaughn": ["slr", "ventus", "velocity", "ion", "vision"]}

# launch years (approximate where a line sold for more than one season)
TABLE = {
    ("ccm", "super tacks", "as1"): 2019, ("ccm", "tacks", "asv"): 2020, ("ccm", "tacks", "asv pro"): 2020,
    ("ccm", "tacks", "as580"): 2020, ("ccm", "tacks", "as"): 2021,
    ("ccm", "tacks", "xf"): 2022, ("ccm", "tacks", "xf pro"): 2022, ("ccm", "tacks", "xf70"): 2022,
    ("ccm", "tacks", "xf80"): 2022, ("ccm", "tacks", "xf90"): 2022,
    ("ccm", "tacks", "xr"): 2024, ("ccm", "tacks", "xr pro"): 2024, ("ccm", "tacks", "xr75"): 2024,
    ("ccm", "tacks", "xr80"): 2024, ("ccm", "tacks", "xr85"): 2024,
    ("ccm", "jetspeed", "ft2"): 2019, ("ccm", "jetspeed", "ft3 pro"): 2020,
    ("ccm", "jetspeed", "ft4"): 2021, ("ccm", "jetspeed", "ft4 pro"): 2021,
    ("ccm", "jetspeed", "ft5"): 2022, ("ccm", "jetspeed", "ft5 pro"): 2022,
    ("ccm", "jetspeed", "ft6"): 2023, ("ccm", "jetspeed", "ft6 pro"): 2023, ("ccm", "jetspeed", "ft670"): 2023,
    ("ccm", "jetspeed", "ft675"): 2023, ("ccm", "jetspeed", "ft680"): 2023, ("ccm", "jetspeed", "ft690"): 2023,
    ("ccm", "jetspeed", "ft7"): 2024, ("ccm", "jetspeed", "ft7 pro"): 2024,
    ("ccm", "jetspeed", "ft8"): 2025, ("ccm", "jetspeed", "ft8 pro"): 2025, ("ccm", "jetspeed", "ft860"): 2025,
    ("ccm", "jetspeed", "ft870"): 2025, ("ccm", "jetspeed", "ft880"): 2025, ("ccm", "jetspeed", "ft890"): 2025,
    ("ccm", "jetspeed", "ft9 pro"): 2026, ("ccm", "jetspeed", "ftw pro"): 2026,
    ("ccm", "ribcor", "trigger 4 pro"): 2019, ("ccm", "ribcor", "trigger 5 pro"): 2020,
    ("ccm", "ribcor", "trigger 6"): 2021, ("ccm", "ribcor", "trigger 7 pro"): 2022,
    ("ccm", "ribcor", "trigger 8"): 2023, ("ccm", "ribcor", "trigger 8 pro"): 2023,
    ("ccm", "ribcor", "trigger 9"): 2024, ("ccm", "ribcor", "trigger 9 pro"): 2024,
    ("ccm", "ribcor", "trigger 10 pro"): 2025,
    ("ccm", "eflex", "5.5"): 2020, ("ccm", "eflex", "5.9"): 2020,
    ("ccm", "eflex", "6"): 2023, ("ccm", "eflex", "6 pro"): 2023, ("ccm", "eflex", "6.5"): 2023,
    ("ccm", "eflex", "6.9"): 2023, ("ccm", "eflex", "e6.5"): 2023, ("ccm", "eflex", "e6.9"): 2023,
    ("ccm", "eflex", "7 pro"): 2025,
    ("true", "catalyst", "9x"): 2020, ("true", "catalyst", "7x"): 2020,
    ("true", "catalyst", "9x3"): 2022, ("true", "catalyst", "7x3"): 2022, ("true", "catalyst", "5x3"): 2022,
    ("true", "catalyst", "3x3"): 2022, ("true", "catalyst", "3x4"): 2024, ("true", "catalyst", "5x5"): 2025,
    ("true", "catalyst", "3x6"): 2026,
    ("true", "hzrdus", "9x"): 2023, ("true", "hzrdus", "7x"): 2023, ("true", "hzrdus", "5x"): 2023,
    ("true", "hzrdus", "3x4"): 2024, ("true", "hzrdus", "7x5"): 2025, ("true", "hzrdus", "5x5"): 2025,
    ("true", "hzrdus", "3x5"): 2025,
    ("vaughn", "ventus", "slr4"): 2023, ("vaughn", "ventus", "slr4 pro"): 2023,
    ("vaughn", "ventus", "slr4 pro carbon"): 2023,
    ("vaughn", "velocity", "v10"): 2021, ("vaughn", "velocity", "v10 pro"): 2021,
    ("vaughn", "velocity", "v10 pro carbon"): 2021,
}


def explicit_year(name, url):
    m = re.search(r"\b(20(?:1\d|2[0-7]))\b", name)
    if m:
        return int(m.group(1))
    m = re.search(r"'(1\d|2[0-7])\b", name)
    if m:
        return 2000 + int(m.group(1))
    m = re.search(r"(?<![a-z] )\(?\bS(2[2-7])\b\)?", name, re.I)
    if m:
        return 2000 + int(m.group(1))
    if "monkey.com" in url:
        m = re.search(r"-(1[5-9]|2[0-7])(?:-[a-z]+)?\.html$", url)
        if m:
            return 2000 + int(m.group(1))
    return None


def model_key(brand, name):
    b = (brand or "").lower()
    if b not in LINE_WORDS:
        return None
    n = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", name.lower())
    n = re.sub(r"\b(20\d\d|s2\d)\b", " ", n)
    n = n.replace("extreme flex", "eflex").replace("e-flex", "eflex").replace("e flex", "eflex")
    n = re.sub(r"\bas-?v\b", "asv", n)
    n = re.sub(r"\b(as|ft|xf|xr|slr)[\s-]+(?=\d)", r"\1", n)  # "AS 580" "FT 6" "XF 90" -> as580 ft6 xf90
    toks = re.findall(r"[a-z0-9.+]+", n.replace("-", " "))
    for lw in LINE_WORDS[b]:
        parts = lw.split()
        for i in range(len(toks) - len(parts) + 1):
            if toks[i:i + len(parts)] == parts:
                code = []
                for t in toks[i + len(parts):i + len(parts) + 3]:
                    if t in STOP or not GEN.match(t):
                        break
                    code.append(t)
                if lw == "ventus" or lw == "slr":
                    lw = "ventus"
                return (b, lw, " ".join(code)) if code else None
    return None


def assign(items):
    """Set d["year"] ("2025" or "2023~" when approximate) on new CCM/True/Vaughn items; others get ""."""
    todo = [d for d in items if d.get("cond") == "New" and d.get("brand") in BRANDS]
    evidence = collections.defaultdict(collections.Counter)
    for d in todo:
        d["_ey"] = explicit_year(d["name"], d["url"])
        d["_mk"] = model_key(d["brand"], d["name"])
        if d["_ey"] and d["_mk"]:
            evidence[d["_mk"]][d["_ey"]] += 1
    agreed = {}
    for k, c in evidence.items():
        y, n = c.most_common(1)[0]
        if n >= 0.7 * sum(c.values()):
            agreed[k] = y
    for d in items:
        d["year"] = ""
    for d in todo:
        if d["_ey"]:
            d["year"] = str(d["_ey"])
        elif d["_mk"] in agreed:
            d["year"] = str(agreed[d["_mk"]])
        elif d["_mk"] in TABLE:
            d["year"] = f"{TABLE[d['_mk']]}~"
        d.pop("_ey", None); d.pop("_mk", None)
