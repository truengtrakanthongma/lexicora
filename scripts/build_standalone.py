"""Fold index.html and every asset it loads into one self-contained page.

The game normally fetches assets/*.png and assets/props.js over HTTP. A page
published as an Artifact is served alone, with a CSP that blocks every host but
Google Fonts, so anything it needs has to already be inside the file. This
script inlines the prop metadata and turns each atlas into a data: URI.

The Artifact runtime supplies <!doctype html>, <head> and <body> itself, so the
output carries only what goes inside them - the <title>, the font link, the
stylesheet and the markup.

Run:  python3 scripts/build_standalone.py [out.html]
"""
import base64, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "index.html")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "lexicora-standalone.html")

html = open(SRC, encoding="utf-8").read()

# ---- pull the pieces the Artifact wrapper does not supply -------------------
head = html[html.index("<head>") + len("<head>"):html.index("</head>")]
body = html[html.index("<body>") + len("<body>"):html.index("</body>")]

# Match each kind of tag on its own terms. A single alternation with a lazy
# quantifier matches the bare "<style>" and silently drops the whole
# stylesheet, which publishes an unstyled blank page.
HEAD_TAGS = re.compile(
    r"<title\b[^>]*>.*?</title>"
    r"|<style\b[^>]*>.*?</style>"
    r"|<link\b[^>]*>", re.S)
keep = []
for tag in HEAD_TAGS.findall(head):
    # charset and viewport come from the wrapper; preconnect hints are noise
    # once the only remaining request is the stylesheet itself
    if "preconnect" in tag:
        continue
    keep.append(tag)
if not any(t.startswith("<style") and len(t) > 200 for t in keep):
    sys.exit("the stylesheet did not survive extraction")
if not any(t.startswith("<title") for t in keep):
    sys.exit("no <title> found — the artifact would be named after the file")
head_kept = "\n".join(keep)

# ---- inline the prop metadata ----------------------------------------------
props_js = open(os.path.join(ROOT, "assets", "props.js"), encoding="utf-8").read()
body = body.replace('<script src="assets/props.js"></script>',
                    "<script>\n" + props_js.strip() + "\n</script>")

# ---- inline every atlas the loader names -----------------------------------
def data_uri(rel):
    path = os.path.join(ROOT, rel)
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


inlined, missing = 0, []
# The loader builds its paths in two ways: literal 'assets/x.png' strings and
# `assets/player_${k}_s${i}.png` templates. Expand the templates first so the
# literal pass can see every one of them.
def expand(match):
    tpl = match.group(1)
    return tpl  # handled below; kept for clarity of intent


CLASS_KEYS = ["hero", "archer", "mage"]
template_pairs = []
for k in CLASS_KEYS:
    for i in range(4):
        template_pairs.append((f"assets/player_{k}_s{i}.png", f"{k}{i}"))
        template_pairs.append((f"assets/battle_{k}_s{i}.png", f"battle_{k}{i}"))

# Replace the two template lines with an explicit map, so nothing is built from
# string interpolation any more and every source is a data: URI.
tpl_block = """  for(const k of CLASS_KEYS) for(let i=0;i<4;i++){
    files[k+i] = `assets/player_${k}_s${i}.png`;
    files['battle_'+k+i] = `assets/battle_${k}_s${i}.png`;
  }"""
if tpl_block not in body:
    sys.exit("loader shape changed: the per-class template block was not found")
explicit = "\n".join(
    f"  files[{key!r}] = {data_uri(path)!r};" for path, key in template_pairs)
body = body.replace(tpl_block, explicit)
inlined += len(template_pairs)

# Now every remaining asset path is a plain quoted literal.
def sub_literal(m):
    global inlined
    quote, rel = m.group(1), m.group(2)
    if not os.path.exists(os.path.join(ROOT, rel)):
        missing.append(rel)
        return m.group(0)
    inlined += 1
    return quote + data_uri(rel) + quote


body = re.sub(r"(['\"])(assets/[A-Za-z0-9_./-]+\.png)\1", sub_literal, body)

if missing:
    sys.exit("missing assets: " + ", ".join(sorted(set(missing))))
# Only quoted paths would actually be fetched; prose mentions in comments are
# fine and worth keeping, since they say where the data came from.
left = re.findall(r"""['"](assets/[A-Za-z0-9_./-]+)['"]""", body)
if left:
    sys.exit("still referencing files on disk: " + ", ".join(sorted(set(left))))

out = head_kept + "\n" + body
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out)

mb = len(out.encode("utf-8")) / 1048576
print(f"{OUT}  {mb:.2f} MB  ({inlined} assets inlined)")
if mb > 15:
    print("  ! close to the 16 MB artifact limit")
