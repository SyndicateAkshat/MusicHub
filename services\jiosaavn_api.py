import html
import requests

JIOSAAVN_ENDPOINTS = [
    "https://jiosaavn-api-beta.vercel.app/search/songs",
    "https://jiosaavn-api-rho.vercel.app/search/songs",
    "https://saavn.me/api/search/songs",
]
TIMEOUT = 6


def _extract_link(items):
    if isinstance(items, list):
        for item in reversed(items):
            if isinstance(item, dict):
                link = item.get("link") or item.get("url")
                if link and str(link).startswith("http"):
                    return str(link)
    elif isinstance(items, str) and items.startswith("http"):
        return items
    return None


def search_songs(query: str, limit: int = 25) -> list[dict]:
    """Search online music (iTunes + JioSaavn API mirrors)."""
    query = query.strip()
    if not query:
        return []

    songs, seen_urls = [], set()

    # 1. Search iTunes Music API
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "media": "music", "entity": "song", "limit": limit},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            for item in resp.json().get("results", []):
                stream_url = item.get("previewUrl")
                if not stream_url or stream_url in seen_urls:
                    continue
                seen_urls.add(stream_url)
                raw_art = item.get("artworkUrl100") or ""
                dur_ms = item.get("trackTimeMillis")
                songs.append({
                    "id": f"itunes_{item.get('trackId')}",
                    "title": html.unescape(item.get("trackName") or "Unknown Title"),
                    "artist": html.unescape(item.get("artistName") or "Unknown Artist"),
                    "album": html.unescape(item.get("collectionName") or ""),
                    "image_url": raw_art.replace("100x100bb", "600x600bb") if raw_art else None,
                    "stream_url": stream_url,
                    "duration": int(dur_ms // 1000) if dur_ms else None,
                })
    except Exception:
        pass

    # 2. Search JioSaavn API mirrors
    for endpoint in JIOSAAVN_ENDPOINTS:
        if len(songs) >= limit * 2:
            break
        try:
            resp = requests.get(endpoint, params={"query": query, "limit": limit}, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            data = resp.json().get("data", {})
            results = data.get("results", []) if isinstance(data, dict) else data
            if not isinstance(results, list):
                continue

            for item in results:
                stream_url = _extract_link(item.get("downloadUrl") or item.get("download_url"))
                if not stream_url or stream_url in seen_urls:
                    continue

                try:
                    head = requests.head(stream_url, timeout=2, allow_redirects=True)
                    if head.status_code not in (200, 206, 302):
                        continue
                except Exception:
                    continue

                seen_urls.add(stream_url)
                album_data = item.get("album")
                raw_album = album_data.get("name", "") if isinstance(album_data, dict) else (album_data or "")
                artist = item.get("primaryArtists") or item.get("singers") or item.get("artist") or "Unknown Artist"

                dur = item.get("duration")
                try:
                    duration = int(dur) if dur is not None else None
                except (ValueError, TypeError):
                    duration = None

                songs.append({
                    "id": str(item.get("id")),
                    "title": html.unescape(item.get("name") or item.get("title") or "Unknown Title"),
                    "artist": html.unescape(str(artist)),
                    "album": html.unescape(str(raw_album)),
                    "image_url": _extract_link(item.get("image")),
                    "stream_url": stream_url,
                    "duration": duration,
                })
        except Exception:
            continue

    return songs[:limit]