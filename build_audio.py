"""Sync the audio/ folder to the play buttons already in index.html.

This is a dev-time tool, not part of the site. The site is static HTML + CSS +
the .mp3 files; you never run this to view or deploy it.

A word in the phonology "Sound shifts" table is playable because it is wrapped,
in the HTML, as:

    <button class="pw" data-src="audio/de-haus.mp3">Haus</button>
    <button class="pw" data-src="audio/ch-haus.mp3" data-say="Haus">Huus</button>

The HTML is the source of truth. This script reads those buttons and makes the
audio/ folder match: it synthesizes any referenced file that is missing and
deletes any file no longer referenced. It never edits the HTML, so adding or
removing audio is a plain HTML edit (wrap or unwrap a word), then a re-run.

Voice comes from the filename prefix: "de-" is the German voice, "ch-" the Swiss
voice. The text spoken is data-say if present, else the button's visible text.
Standard-column words speak themselves; Zürich-column words carry data-say with
the standard word, because the Swiss voice is fed the same word and shifts it.

Usage: uv run build_audio.py
"""

import re
import subprocess
from pathlib import Path

VOICES = {"de": "de-DE-KatjaNeural", "ch": "de-CH-LeniNeural"}
ROOT = Path(__file__).parent
HTML = ROOT / "index.html"
AUDIO_DIR = ROOT / "audio"

BUTTON_RE = re.compile(
    r'<button class="pw"[^>]*\bdata-src="audio/([^"]+)"[^>]*>(.*?)</button>'
)
SAY_RE = re.compile(r'data-say="([^"]*)"')


def main() -> None:
    AUDIO_DIR.mkdir(exist_ok=True)
    doc = HTML.read_text(encoding="utf-8")

    used = set()
    for m in BUTTON_RE.finditer(doc):
        name, inner = m.group(1), m.group(2)
        used.add(name)
        say = SAY_RE.search(m.group(0))
        text = say.group(1) if say else inner.strip()
        voice = VOICES[name.split("-", 1)[0]]
        path = AUDIO_DIR / name
        if not path.exists():
            print(f"synth: {name}  ({voice})  {text}")
            subprocess.run(
                ["uvx", "edge-tts", "--voice", voice,
                 "--text", text, "--write-media", str(path)],
                check=True,
            )

    for f in AUDIO_DIR.glob("*.mp3"):
        if f.name not in used:
            f.unlink()
            print(f"pruned: {f.name}")

    print(f"in sync: {len(used)} clips referenced by the page")


if __name__ == "__main__":
    main()
