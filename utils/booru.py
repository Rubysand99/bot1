import aiohttp
import random
from typing import Optional

# ── Source definitions ───────────────────────────────────
SOURCES = {
    "gelbooru": {
        "url": "https://gelbooru.com/index.php",
        "params": lambda tags, limit: {
            "page": "dapi", "s": "post", "q": "index",
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20)
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
            "json": 1, "tags": tags, "limit": limit, "pid": random.randint(0, 20)
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
    """
    Lấy 1 post từ danh sách sources, tránh trùng với seen_ids.
    Trả về dict post hoặc None nếu không tìm được.
    """
    if seen_ids is None:
        seen_ids = set()

    # Shuffle để random nguồn mỗi lần
    shuffled = sources[:]
    random.shuffle(shuffled)

    async with aiohttp.ClientSession() as session:
        for source_name in shuffled:
            src = SOURCES.get(source_name)
            if not src:
                continue

            try:
                params = src["params"](tags, limit)
                async with session.get(src["url"], params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
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
