import os
from PIL import Image

# Prefer canonical resources location; fall back to docs/
OUT_DIR = os.path.join('resources', 'icons')
os.makedirs(OUT_DIR, exist_ok=True)

src_candidates = [
    os.path.join(OUT_DIR, 'datamonitor_logo_icon.png'),
    os.path.join('docs', 'datamonitor_logo_icon.png'),
]

src = None
for c in src_candidates:
    if os.path.exists(c):
        src = c
        break

if src is None:
    raise FileNotFoundError(
        'No source PNG found for icon generation. Please place datamonitor_logo_icon.png in resources/icons/ or docs/'
    )

dst = os.path.join(OUT_DIR, 'datamonitor.ico')

# sizes for .ico (Pillow will pack multiple sizes)
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

img = Image.open(src).convert('RGBA')
img.save(dst, sizes=sizes)
print(f'Wrote {dst}')
