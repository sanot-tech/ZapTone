"""
🏷️ tags.py - guess music tags from a file name.

Example:  "Artist - Album - Song (2024) [Live].mp4"
Becomes:  artist=Artist, album=Album, title=Song, date=2024, comment=[Live]

Why do this: people save videos like that, and a music player
shows the tags. Without them every track is called "Video_2024".
"""

from __future__ import annotations

import re

# 📐 patterns we clean out of the title, in this order
_YEAR_IN_BRACKETS = re.compile(r"[([](\d{4})[)\]]")          # "(2024)" or "[2024]"
_TAIL_BRACKETS = re.compile(r"([(][^()]*[)]|\[[^\]]*\])\s*$")  # "(Live)" at the end
_SPACES = re.compile(r"\s+")                                 # many spaces -> one
_EDGES = re.compile(r"^ | $")                                 # cut off edges
_EXT = re.compile(r"\.[A-Za-z0-9]{2,4}$")                     # ".mp4" at the end


def tags_from_filename(filename: str) -> dict[str, str]:
    """🎼 Read a file name and return a dict of tags. Never raises."""
    # 🪓 1. drop the extension, then turn dots and underscores into spaces
    name = _EXT.sub("", str(filename))
    name = name.replace("_", " ").replace(".", " ")
    name = _SPACES.sub(" ", name).strip(" ")

    # 🏷️ 2. split on " - ":  artist - album - title   (parts are optional)
    artist = album = ""
    parts = [p.strip(" ") for p in name.split(" - ") if p.strip(" ")]
    if len(parts) >= 2:
        artist = parts[0]
    if len(parts) >= 3:
        album = parts[1]
        title = " - ".join(parts[2:])          # keep extra dashes inside the title
    elif len(parts) == 2:
        title = parts[1]
    else:
        title = name

    # 📅 3. a year in brackets becomes the date, and leaves the title
    year = ""
    found = _YEAR_IN_BRACKETS.search(title)
    if found:
        year = found.group(1)
        title = _YEAR_IN_BRACKETS.sub("", title)

    # 💬 4. a tail bracket group goes to the comment:  (Live), [Remix]
    comment = ""
    tail = _TAIL_BRACKETS.search(title)
    if tail:
        comment = tail.group(1)
        title = title[: tail.start()]

    # 🧼 5. final clean up of empty spaces
    title = _EDGES.sub("", _SPACES.sub(" ", title))

    # 📤 6. build the result, skipping empty values so ffmpeg stays quiet
    result = {"title": title, "artist": artist, "album": album, "date": year, "comment": comment}
    return {k: v for k, v in result.items() if v}