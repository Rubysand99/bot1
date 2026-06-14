import aiohttp
import random
from typing import Optional

# ── Gelbooru-style API ───────────────────────────────────
def _gelbooru_params(tags, limit):
    return {
        "page": "dapi", "s": "post", "q": "index",
        "json": 1, "tags": tags, "limit": limit,
        "pid": random.randint(0, 20)
    }

def _gelbooru_parse(data):
    if isinstance(data, dict):
        return data.get("post", [])
    return []

def _gelbooru_extract(prefix, p):
    return {
        "id": f"{prefix}_{p['id']}",
        "url": p["file_url"],
        "source": prefix.capitalize(),
        "type": _get_type(p["file_url"])
    }

# ── Moebooru-style API (konachan, yande.re) ──────────────
def _moebooru_params(tags, limit):
    return {
        "tags": tags, "limit": limit,
        "page": random.randint(1, 20)
    }

def _moebooru_parse(data):
    return data if isinstance(data, list) else []

def _moebooru_extract(prefix, p):
    url = p.get("file_url", "")
    return {
        "id": f"{prefix}_{p['id']}",
        "url": url,
        "source": prefix.capitalize(),
        "type": _get_type(url)
    }

# ── Sources ──────────────────────────────────────────────
SOURCES = {
    # Gelbooru-style
    "gelbooru": {
        "url": "https://gelbooru.com/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": _gelbooru_parse,
        "extract": lambda p: _gelbooru_extract("gelbooru", p)
    },
    "rule34": {
        "url": "https://api.rule34.xxx/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: _gelbooru_extract("rule34", p)
    },
    "xbooru": {
        "url": "https://xbooru.com/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: _gelbooru_extract("xbooru", p)
    },
    "tbib": {
        "url": "https://tbib.org/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: _gelbooru_extract("tbib", p)
    },
    "realbooru": {
        "url": "https://realbooru.com/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: _gelbooru_extract("realbooru", p)
    },
    "hypnohub": {
        "url": "https://hypnohub.net/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: _gelbooru_extract("hypnohub", p)
    },
    "safebooru": {
        "url": "https://safebooru.org/index.php",
        "params": lambda t, l: _gelbooru_params(t, l),
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: {
            "id": f"safebooru_{p['id']}",
            "url": f"https://safebooru.org/images/{p['directory']}/{p['image']}",
            "source": "Safebooru",
            "type": _get_type(p.get("image", ""))
        }
    },
    # Danbooru-style (giới hạn 2 tags free)
    "danbooru": {
        "url": "https://danbooru.donmai.us/posts.json",
        "params": lambda t, l: {
            "tags": " ".join(t.split()[:2]) if t else "",
            "limit": l, "page": random.randint(1, 10)
        },
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: {
            "id": f"danbooru_{p['id']}",
            "url": p.get("file_url") or p.get("large_file_url", ""),
            "source": "Danbooru",
            "type": _get_type(p.get("file_url", ""))
        }
    },
    # Moebooru-style
    "konachan": {
        "url": "https://konachan.com/post.json",
        "params": lambda t, l: _moebooru_params(t, l),
        "parse": _moebooru_parse,
        "extract": lambda p: _moebooru_extract("konachan", p)
    },
    "yandere": {
        "url": "https://yande.re/post.json",
        "params": lambda t, l: _moebooru_params(t, l),
        "parse": _moebooru_parse,
        "extract": lambda p: _moebooru_extract("yandere", p)
    },
}

VALID_SOURCES = list(SOURCES.keys())

# Mặc định chỉ dùng NSFW sources
DEFAULT_SOURCES = ["gelbooru", "rule34", "xbooru", "tbib", "konachan", "yandere"]

def _get_type(url: str) -> str:
    url = url.lower()
    if url.endswith(".mp4") or url.endswith(".webm"):
        return "video"
    elif url.endswith(".gif"):
        return "gif"
    return "image"


async def fetch_post(
    sources: list[str],
    tags: str = "",
    seen_ids: set = None,
    limit: int = 30
) -> Optional[dict]:
    if seen_ids is None:
        seen_ids = set()

    shuffled = sources[:]
    random.shuffle(shuffled)

    async with aiohttp.ClientSession() as session:
        for source_name in shuffled:
            src = SOURCES.get(source_name)
            if not src:
                continue

            try:
                params = src["params"](tags, limit)
                async with session.get(
                    src["url"], params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    if r.status != 200:
                        continue
                    raw = await r.json(content_type=None)

                posts = src["parse"](raw)
                if not posts:
                    continue

                random.shuffle(posts)

                for p in posts:
                    try:
                        post = src["extract"](p)
                    except (KeyError, TypeError):
                        continue

                    if not post["url"]:
                        continue
                    if post["id"] in seen_ids:
                        continue

                    return post

            except Exception as e:
                print(f"[BOORU] Error fetching from {source_name}: {e}")
                continue

    return None
