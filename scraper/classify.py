"""Brand / category / line / sub-type rules shared by every store."""
import re

BRANDS = ["Shock Doctor", "Tovi", "Daoust", "Marsblade", "HockeyShot", "Labeda", "Volt", "Brian's", "Brians",
          "Pro Blackout", "CCM", "Bauer", "True", "TRUE", "Warrior", "Sherwood", "Vaughn", "Graf", "Easton",
          "Reebok", "Mission", "Alkali", "Tour", "TPS", "TronX", "Tackla", "Winnwell", "Mylec", "STX",
          "Franklin", "A&R", "Pure Hockey", "Jackson", "Fischer", "Sportmask", "Howies", "Elite"]
BRAND_FIX = {"TRUE": "True", "Brians": "Brian's", "SportMask": "Sportmask", "BAUER": "Bauer"}


def brand(n):
    best = None
    for b in BRANDS:
        m = re.search(r"(?<![A-Za-z])" + re.escape(b) + r"(?![A-Za-z])", n)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), b)
    b = best[1] if best else (n.split() or [""])[0]
    b = BRAND_FIX.get(b, b)
    return b[:1].upper() + b[1:] if b.islower() else b


def cat(n):
    l = n.lower()
    if "goalie" in l:
        return "Goalie"
    if re.search(r"tape|runner|chassis|blade guard|wheels", l):
        return "Accessories"
    if re.search(r"helmet|facemask|face shield|full shield|half shield|visor|\bcage\b|splash guard", l):
        return "Helmets"
    if re.search(r"\bpants?\b|girdle|pant shell|breezers?", l):
        return "Pants"
    if re.search(r"backpack|duffel|equipment bag|carry bag|wheel bag|wheeled", l):
        return "Bags"
    for k, v in [("skate", "Skates"), ("stick", "Sticks"), ("glove", "Gloves"), ("helmet", "Helmets"),
                 ("shin", "Shin guards"), ("elbow", "Elbow pads"), ("shoulder", "Shoulder pads"),
                 ("jock", "Accessories"), ("pants", "Pants"), ("bag", "Bags")]:
        if k in l and not (k == "stick" and "stickhandling" in l):
            return v
    return "Accessories"


LINES = [("Pro Blackout", "Pro Blackout"), ("Tacks", "Tacks"), ("Jetspeed|JetSpeed|JETSPEED", "Jetspeed"), ("Ribcor", "Ribcor"),
         (r"\bNext\b|\bNEXT\b", "Next"), ("Axis", "Axis"), ("EFLEX|Extreme Flex|Eflex|E-Flex", "EFLEX"),
         ("Retro Flex", "Retro Flex"), ("YTFlex", "YTFlex"), ("Phenom", "Phenom"),
         ("Supreme|SUPREME", "Supreme"), ("Vapor|VAPOR", "Vapor"), ("Nexus|NEXUS", "Nexus"), ("Proto", "Proto"),
         ("Pulse", "Pulse"), (r"\bFuse\b|\bFUSE\b", "Fuse"), ("GSX", "GSX"), ("Reactor", "Reactor"),
         ("SV-Pro", "SV-Pro"), ("Konekt", "Konekt"), ("Re-Akt", "Re-Akt"), ("Profile", "Profile"),
         ("X-LS", "X-LS"), ("X-LP", "X-LP"), ("RSX", "RSX"), ("Whistler", "Whistler"), ("Tactical", "Tactical"),
         (r"\bNSX\b", "NS"), ("Mega", "Mega"), (r"Bauer X Senior", "X"),
         ("HZRDUS", "HZRDUS"), ("Catalyst", "Catalyst"), (r"\bTF\d", "TF"), (r"\bL95\b|L12", "L-Series"),
         ("Project X", "Project X"), ("Covert", "Covert"), ("Alpha|ALPHA", "Alpha"), ("LX2", "Alpha"),
         ("Novium", "Novium"), ("Ritual", "Ritual"), ("Swagger", "Swagger"),
         ("Code", "Code"), ("REKKER|Rekker", "Rekker"), (r"\bT120\b|T9\.0", "T-Series"), ("Project", "Project"),
         ("EK3", "EK"), ("PMP", "PMP"), ("Pro Mystery", "Pro Mystery"),
         (r"SLR\d|Ventus", "SLR / Ventus"), (r"Velocity|V10|VX1|V9", "Velocity"), (r"\bIon\b|\bION\b", "Ion"),
         ("Pro V Elite", "Pro V"), ("Iconik", "Iconik"), ("Optik", "Optik"), ("GX6", "GX6"), (r"DM10", "DM"),
         ("Response", "Response"), ("RPD", "RPD"), ("X-Fit", "X-Fit"), ("951", "951"), ("Prodigy", "Prodigy"),
         ("Synergy", "Synergy"), (r"EQ\d|S3", "Synergy / Stealth"), ("Premier", "Premier"),
         ("Inhaler", "Inhaler"), ("Revel|Cele", "Revel / Cele")]


def line(n):
    for p, v in LINES:
        if re.search(p, n):
            return v
    return ""


def sub(name, c, play):
    n = name.lower()
    if c == "Goalie":
        # most stores say "Goalie Pads" rather than "Leg Pads"
        if re.search(r"\bpads?\b|pad set", n) and not re.search(
                r"knee|strap|buckle|\btoe\b|lace|padded|\bbag|cover|chest|\barm|pant|shin|thigh guard|jock|neck", n):
            return "Leg pads"
        for k, v in [("leg pad", "Leg pads"), ("blocker", "Blocker"), ("catch", "Catch glove"),
                     ("trapper", "Catch glove"), ("glove", "Catch glove"), ("combo", "Full set"),
                     ("skate", "Goalie skates"), ("pant", "Goalie pants"), ("chest", "Chest & arm"),
                     ("body armo", "Chest & arm"), ("stick", "Goalie stick"), ("mask", "Mask"), ("helmet", "Mask")]:
            if k in n:
                return v
        return "Other goalie"
    if c == "Accessories":
        for k, v in [("tape", "Tape"), ("runner", "Runners & steel"), ("steel", "Runners & steel"),
                     ("chassis", "Runners & steel"), ("guard", "Skate guards"), ("puck", "Pucks"),
                     ("wheel", "Wheels & bearings"), ("bearing", "Wheels & bearings"), ("sock", "Socks"),
                     ("jock", "Jocks"), ("dryer", "Gear care"), ("dangler", "Training aids"),
                     ("trainer", "Training aids")]:
            if k in n:
                return v
        return "Other"
    if c == "Helmets":
        if "helmet" in n and not re.search(r"facemask|face mask$", n):
            return "Combo (with cage)" if re.search(r"combo|with cage|with facemask", n) else "Helmet only"
        return "Cage / visor / shield"
    if c == "Skates":
        if " rec " in f" {n} " or "recreational" in n:
            return "Recreational"
        return "Roller skates" if play == "Roller" else "Ice skates"
    if c == "Pants":
        return "Roller pants" if play == "Roller" else "Ice pants"
    if c == "Sticks":
        return "Grip" if "grip" in n else "Standard / non-grip"
    return ""


JUNK = re.compile(r"jersey|hoodie|polo|basketball|baseball|softball|lacrosse|football|soccer|\bsocks?\b|t-shirt|"
                  r"\btee\b|\bhat\b|beanie|toque|\bcap\b|jacket|sweat|jogger|leggings|gift ?card|your design|"
                  r"reorder|custom|lanyard|keychain|sticker|\bmini\b|towel|ringette|referee|base ?layer|"
                  r"long sleeve|short sleeve|decal|poster|\bmug\b|tumbler|figurine|cleats?|sandal|shoe|\bbat\b|"
                  r"batting|catcher'?s (?:mask|gear)|\bfee\b|floorball|floor hockey|novelty|souvenir|pajama|"
                  r"car flag|pinnie|sharpening|water bottle|field hockey|figure skat|broomball", re.I)


def is_junk(name):
    return bool(JUNK.search(name)) and not re.search(r"goalie (?:catch|glove|pad|blocker)", name, re.I)


def level(n):
    for x, pats in [("Senior", r"\bsenior\b|\bsr\b"), ("Intermediate", r"\bintermediate\b|\bint\b"),
                    ("Junior", r"\bjunior\b|\bjr\b"), ("Youth", r"\byouth\b|\byth\b|\byt\b")]:
        if re.search(pats, n, re.I):
            return x
    return ""
