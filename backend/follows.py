import httpx
from bs4 import BeautifulSoup

async def get_follows(user: str):
    url = f"https://tools.2807.eu/follows?user={user}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers={"User-Agent":"Ludik/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    # Generic table rows parsing
    for tr in soup.select("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 3:
            img = tds[0].find("img")
            avatar = img["src"] if img and img.get("src") else None
            name = tds[1].get_text(strip=True)
            date = tds[2].get_text(strip=True)
            if name:
                a = tds[1].find("a")
                url = a["href"] if a and a.get("href") else None
                items.append({"channel": name, "channel_url": url, "avatar": avatar, "followed_at": date})
    # Fallback: anchors
    if not items:
        for a in soup.find_all("a", href=True):
            if "twitch.tv/" in a["href"]:
                items.append({"channel": a.get_text(strip=True), "channel_url": a["href"], "avatar": None, "followed_at": None})
    return {"user": user, "follows": items}
