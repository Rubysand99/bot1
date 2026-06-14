import aiohttp
import random
from typing import Optional

SOURCES = {
    "gelbooru": {
        "url": "https://gelbooru.com/index.php",
        "params": lambda tags, limit: {
            "page": "dapi", "s": "post", "q": "index",
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20)
        },
        "parse": lambda data: data.get("post", []) if isinstance(data, dict) else [],
        "extract": lambda p: {
            "id": f"gelbooru_{p['id']}",
            "url": p["file_url"],
            "source": "Gelbooru",
            "type": _get_type(p["file_url"])
        }
    },
    "rule34": {
        "url": "https://api.rule34.xxx/index.php",
        "params": lambda tags, limit: {
            "page": "dapi", "s": "post", "q": "index",
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20)
        },
        "parse": lambda data: data if isinstance(data, list) else [],
        "extract": lambda p: {
            "id": f"rule34_{p['id']}",
            "url": p["file_url"],
            "source": "Rule34",
            "type": _get_type(p["file_url"])
        }
    },
    "danbooru": {
        "url": "https://danbooru.donmai.us/posts.json",
        # Danbooru free chỉ cho tối đa 2 tags → tự trim
        "params": lambda tags, limit: {
            "tags": " ".join(tags.split()[:2]) if tags else "",
            "limit": limit,
            "page": random.randint(1, 10)
        },
        "parse": lambda data: data if isinstance(data, list) else [],
        "extract": lambda p: {
            "id": f"danbooru_{p['id']}",
            "url": p.get("file_url") or p.get("large_file_url", ""),
            "source": "Danbooru",
            "type": _get_type(p.get("file_url", ""))
        }
    },
    "safebooru": {
        "url": "https://safebooru.org/index.php",
        "params": lambda tags, limit: {
            "page": "dapi", "s": "post", "q": "index",
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20)
        },
        "parse": lambda data: data if isinstance(data, list) else [],
        "extract": lambda p: {
            "id": f"safebooru_{p['id']}",
            "url": f"https://safebooru.org/images/{p['directory']}/{p['image']}",
            "source": "Safebooru",
            "type": _get_type(p.get("image", ""))
        }
    }
}

VALID_SOURCES = list(SOURCES.keys())

def _get_type(url: str) -> str:
    url = url.lower()
    if url.endswith(".mp4") or url.endswith(".webm"):
        return "video"
    elif url.endswith(".gif"):
        return "gif"
    else:
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
