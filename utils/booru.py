import aiohttp
import random
from typing import Optional

# ── Source definitions ───────────────────────────────────
SOURCES = {
    "gelbooru": {
        "url": "https://gelbooru.com/index.php",
        "params": lambda tags, limit: {
            "page": "dapi", "s": "post", "q": "index",
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20),
            "api_key": "2dbf7bcbcf7fac730e8acfacedb0b077556d2ed7388aec7802e869e940bdcb90a62e6f6e73f7506fb9b097244cb58ecb4d99e5b1ae9b53457929264ac20ab243",
            "user_id": "6374630"
        },
        "parse": lambda data: data.get("post", []),
        "extract": lambda p: {
            "id": f"gelbooru_{p['id']}",
            "url": p["file_url"],
            "source": "Gelbooru",
            "tags": p.get("tags", ""),
            "type": _get_type(p["file_url"])
        }
    },
    "rule34": {
        "url": "https://api.rule34.xxx/index.php",
        "params": lambda tags, limit: {
            "page": "dapi", "s": "post", "q": "index",
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20),
            "api_key": "925c7c66afa8977398177ad87e83fc5d5c6f71f9c001c4d6d2f8bf4ade1cfc81954fc2e94feedcb0b97e430ec68c5ca4b9d62bed1b4dc216efc0d4da93613d87",
            "user_id": "6374630"
        },
        "parse": lambda data: data if isinstance(data, list) else [],
        "extract": lambda p: {
            "id": f"rule34_{p['id']}",
            "url": p["file_url"],
            "source": "Rule34",
            "tags": p.get("tags", ""),
            "type": _get_type(p["file_url"])
        }
    },
    "danbooru": {
        "url": "https://danbooru.donmai.us/posts.json",
        "params": lambda tags, limit: {
            "tags": tags, "limit": limit,
            "page": random.randint(1, 10)
        },
        "parse": lambda data: data if isinstance(data, list) else [],
        "extract": lambda p: {
            "id": f"danbooru_{p['id']}",
            "url": p.get("file_url", p.get("large_file_url", "")),
            "source": "Danbooru",
            "tags": p.get("tag_string", ""),
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
            "tags": p.get("tags", ""),
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


# ── Main fetch function ──────────────────────────────────
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for source_name in shuffled:
            src = SOURCES.get(source_name)
            if not src:
                continue

            try:
                params = src["params"](tags, limit)
                async with session.get(src["url"], params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        print(f"[BOORU] {source_name} trả về HTTP {r.status}")
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
                print(f"[BOORU] Error fetching from {source_name}: {type(e).__name__}: {e}")
                continue

    return None
