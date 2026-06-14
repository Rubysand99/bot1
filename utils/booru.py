import aiohttp
import random
from typing import Optional

# ── Gelbooru-style params ────────────────────────────────
def _gel_params(tags, limit):
    return {
        "page": "dapi", "s": "post", "q": "index",
        "json": 1, "tags": tags, "limit": limit,
        "pid": random.randint(0, 20)
    }

def _gel_parse(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("post", [])
    return []

def _get_type(url: str) -> str:
    url = url.lower()
    if url.endswith(".mp4") or url.endswith(".webm"):
        return "video"
    elif url.endswith(".gif"):
        return "gif"
    return "image"

# ── Sources ──────────────────────────────────────────────
SOURCES = {
    "xbooru": {
        "url": "https://xbooru.com/index.php",
        "params": lambda t, l: _gel_params(t, l),
        "parse": _gel_parse,
        "extract": lambda p: {
            "id": f"xbooru_{p['id']}",
            "url": p["file_url"],
            "source": "Xbooru",
            "type": _get_type(p["file_url"])
        }
    },
    "tbib": {
        "url": "https://tbib.org/index.php",
        "params": lambda t, l: _gel_params(t, l),
        "parse": _gel_parse,
        "extract": lambda p: {
            "id": f"tbib_{p['id']}",
            "url": f"https://tbib.org/images/{p['directory']}/{p['image']}",
            "source": "TBIB",
            "type": _get_type(p.get("image", ""))
        }
    },
    "hypnohub": {
        "url": "https://hypnohub.net/index.php",
        "params": lambda t, l: _gel_params(t, l),
        "parse": _gel_parse,
        "extract": lambda p: {
            "id": f"hypnohub_{p['id']}",
            "url": p["file_url"],
            "source": "Hypnohub",
            "type": _get_type(p["file_url"])
        }
    },
    "safebooru": {
        "url": "https://safebooru.org/index.php",
        "params": lambda t, l: _gel_params(t, l),
        "parse": _gel_parse,
        "extract": lambda p: {
            "id": f"safebooru_{p['id']}",
            "url": f"https://safebooru.org/images/{p['directory']}/{p['image']}",
            "source": "Safebooru",
            "type": _get_type(p.get("image", ""))
        }
    },
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
    "yandere": {
        "url": "https://yande.re/post.json",
        "params": lambda t, l: {
            "tags": t, "limit": l,
            "page": random.randint(1, 20)
        },
        "parse": lambda d: d if isinstance(d, list) else [],
        "extract": lambda p: {
            "id": f"yandere_{p['id']}",
            "url": p.get("file_url", ""),
            "source": "Yande.re",
            "type": _get_type(p.get("file_url", ""))
        }
    },
}

VALID_SOURCES = list(SOURCES.keys())
DEFAULT_SOURCES = VALID_SOURCES  # Random từ tất cả nguồn

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
