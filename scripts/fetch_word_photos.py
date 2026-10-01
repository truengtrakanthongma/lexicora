"""Fetch a photograph for each picturable word from Wikimedia Commons.

For every word below, take the lead image of the named English Wikipedia
article (or the Commons file given instead), keep it only if its licence lets
the game redistribute it, crop it square, shrink it to 192 px and write

    assets/words/<word>.jpg
    assets/words/photos.js        (the manifest the game reads)

Each manifest entry carries the author, licence and file page, which the game
shows on the enlarged word card - CC BY and CC BY-SA require that credit.

Words that are not a thing you can photograph (happy, believe, already ...)
are deliberately absent and get an emblem in the game instead.

Every image still has to be LOOKED AT before it ships: a lead image is
sometimes a diagram, a painting with people in it, or simply the wrong sense
of the word. Swap a bad one by putting "File:Something.jpg" in OVERRIDE.

Needs network access to en.wikipedia.org, commons.wikimedia.org and
upload.wikimedia.org, and Pillow (pip install pillow).

Run:  python3 scripts/fetch_word_photos.py [--only camel,oasis]
"""
import html, io, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "words")
UA = "LexicoraWordCards/1.0 (classroom game; https://github.com/truengtrakanthongma/lexicora)"
SIZE = 192

# word -> English Wikipedia article whose lead image shows it
ARTICLE = {
    "forest": "Forest", "tree": "Tree", "river": "River", "bird": "Bird", "leaf": "Leaf",
    "path": "Trail", "morning": "Sunrise",
    "hill": "Hill", "grass": "Poaceae", "sheep": "Sheep", "farm": "Farm", "village": "Village",
    "sky": "Sky",
    "desert": "Desert", "sand": "Sand", "camel": "Camel", "oasis": "Oasis", "map": "Map",
    "cave": "Cave", "rock": "Rock (geology)", "torch": "Torch",
    "snow": "Snow", "ice": "Ice", "mountain": "Mountain", "peak": "Summit",
    "fire": "Fire", "flame": "Flame", "smoke": "Smoke", "ash": "Volcanic ash",
    "ruin": "Ruins", "temple": "Temple", "statue": "Statue", "treasure": "Treasure",
    "glow": "Bioluminescence",
    "shadow": "Shadow", "bridge": "Bridge",
    "castle": "Castle", "king": "Crown (headgear)", "throne": "Throne", "sword": "Sword",
}
# word -> "File:..." on Commons, when the article's lead image is not right
OVERRIDE = {}

# licences the game may redistribute (with credit where required)
OK_LICENCE = re.compile(r"^(cc0|public domain|pd\b|pdm|cc by(-sa)? [0-9.]+)", re.I)


def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def api(host, **params):
    params.update(format="json", formatversion="2")
    return json.loads(get(f"https://{host}/w/api.php", params))


def lead_file(article):
    q = api("en.wikipedia.org", action="query", prop="pageimages", piprop="name", titles=article, redirects=1)
    page = q["query"]["pages"][0]
    name = page.get("pageimage")
    return "File:" + name if name else None


def file_info(title):
    q = api("commons.wikimedia.org", action="query", titles=title, prop="imageinfo",
            iiprop="url|extmetadata", iiurlwidth=480)
    page = q["query"]["pages"][0]
    if "imageinfo" not in page:
        return None
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    val = lambda k: html.unescape(re.sub(r"<[^>]+>", "", meta.get(k, {}).get("value", ""))).strip()
    return {
        "thumb": ii.get("thumburl") or ii["url"],
        "page": ii.get("descriptionurl", ""),
        "license": val("LicenseShortName"),
        "artist": re.sub(r"\s+", " ", val("Artist"))[:80] or "Unknown",
    }


def square_jpeg(data):
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    im = im.resize((SIZE, SIZE), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True, progressive=True)
    return buf.getvalue()


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    os.makedirs(OUT, exist_ok=True)
    manifest_path = os.path.join(OUT, "photos.js")
    manifest = {}
    if os.path.exists(manifest_path):
        m = re.search(r"=\s*(\{.*\});", open(manifest_path, encoding="utf-8").read(), re.S)
        if m:
            manifest = json.loads(m.group(1))
    skipped = []
    for word, article in ARTICLE.items():
        if only and word not in only:
            continue
        try:
            title = OVERRIDE.get(word) or lead_file(article)
            info = title and file_info(title)
            if not info:
                skipped.append((word, "no lead image"))
                continue
            if not OK_LICENCE.match(info["license"]):
                skipped.append((word, f"licence {info['license']!r}"))
                continue
            jpg = square_jpeg(get(info["thumb"]))
            with open(os.path.join(OUT, word + ".jpg"), "wb") as f:
                f.write(jpg)
            manifest[word] = {"src": f"assets/words/{word}.jpg", "artist": info["artist"],
                              "license": info["license"], "url": info["page"], "file": title}
            print(f"  {word:10} {len(jpg)//1024:3d} KB  {info['license']:14} {title}")
            time.sleep(0.3)   # be gentle with the API
        except Exception as e:   # one bad word must not lose the rest
            skipped.append((word, str(e)[:80]))
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("// Photographs for the word cards, from Wikimedia Commons. Written by\n"
                "// scripts/fetch_word_photos.py; every entry carries the credit its licence\n"
                "// asks for, and the game shows it on the enlarged word card.\n"
                "window.LEXICORA_WORD_PHOTOS = " + json.dumps(manifest, ensure_ascii=False, indent=1) + ";\n")
    print(f"{len(manifest)} photos in the manifest")
    for w, why in skipped:
        print(f"  skipped {w}: {why}")


if __name__ == "__main__":
    main()
