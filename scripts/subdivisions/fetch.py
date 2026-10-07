#!/usr/bin/env python3
"""Download the pinned Commons revision of each flag into .cache/subdivisions/commons/.

Every download is checked against the SHA-1 recorded in sources.json. When
Commons now serves a newer upload, the pinned revision is looked up in the
file's upload history instead, so a rebuild always starts from the artwork
that was reviewed. If the pinned revision cannot be found, the script stops
rather than build from unreviewed art.

Usage: fetch.py [CODE or COUNTRY ...]
"""

import hashlib
import json
import sys
import time
import urllib.parse

from common import commons_cache_path, http_get, load_sources, select_codes

COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def archived_url(title, wanted_sha1):
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2", "prop": "imageinfo",
        "iiprop": "url|sha1", "iilimit": "max", "titles": "File:" + title,
    })
    page = json.loads(http_get(f"{COMMONS_API}?{query}"))["query"]["pages"][0]
    for revision in page.get("imageinfo", []):
        if revision["sha1"] == wanted_sha1:
            return revision["url"]
    return None


def fetch(code, source):
    path = commons_cache_path(code)
    pinned = source["revision"]["sha1"]
    if path.exists() and sha1(path.read_bytes()) == pinned:
        return "cached"
    data = http_get(source["revision"]["url"])
    if sha1(data) != pinned:
        url = archived_url(source["commons_title"], pinned)
        if url is None:
            sys.exit(f"{code}: Commons no longer has the pinned revision {pinned} of {source['commons_title']!r}")
        data = http_get(url)
        if sha1(data) != pinned:
            sys.exit(f"{code}: download of the archived revision does not match {pinned}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    # Stay well under Wikimedia's rate limits for anonymous clients.
    time.sleep(0.3)
    return "downloaded"


def main():
    sources = load_sources()
    for code in select_codes(sys.argv[1:], sources):
        print(f"{code}: {fetch(code, sources[code])}")


if __name__ == "__main__":
    main()
