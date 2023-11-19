from collections import defaultdict
from string import Template

import aiohttp
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse, HTMLResponse
from bs4 import BeautifulSoup

DYNASTY_BASE_URL = "https://dynasty-scans.com"

client_session = aiohttp.ClientSession()
app = FastAPI(title="dynasty-scans-embed")
app.add_middleware(CORSMiddleware, allow_origins=["*"])


@app.get("/", include_in_schema=False)
async def route_index():
    return RedirectResponse("/docs")


TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>$title</title>
    <meta http-equiv="refresh" content="0; url=$location">
    <meta property="og:title" content="$title"/>
    <meta property="og:site_name" content="dynasty-scans.nsk.sh"/>
    <meta property="og:description" content="$description"/>
    <meta property="og:image" content="$image"/>
    <meta property="og:url" content="$location"/>
    $extra
</head>
<body>
</body>
</html>
""")

LARGE_IMAGE_TAG = """
    <meta name="twitter:card" content="summary_large_image"/>
"""


def build_description(tags_by_category: dict[str, list[str]]) -> str:
    description = []
    if tags_by_category["Doujin"]:
        description.append(f"{' and '.join(tags_by_category['Doujin'])} Doujin.")
    if tags_by_category["Pairing"]:
        description.append(f"Pairing: {' and '.join(tags_by_category['Pairing'])}.")
    if tags_by_category["General"]:
        description.append(f"Tags: {', '.join(tags_by_category['General'])}.")
    if tags_by_category["Author"]:
        description.append(f"By {' and '.join(tags_by_category['Author'])}.")
    if tags_by_category["Scanlator"]:
        description.append(f"Scanned by {' and '.join(tags_by_category['Scanlator'])}.")
    return " ".join(description)


def is_bot(request: Request) -> bool:
    return "BOT" in request.headers.get("User-Agent", "").upper()


@app.get("/chapters/{slug}")
async def route_dynasty_scans_chapters(request: Request, slug: str):
    location = f"{DYNASTY_BASE_URL}/chapters/{slug}?{request.query_params}"
    if not is_bot(request):
        return RedirectResponse(location, status_code=302)

    url = f"{DYNASTY_BASE_URL}/chapters/{slug}.json"
    async with client_session.get(url) as response:
        data = await response.json()

    tags_by_category = defaultdict(list)
    for tag in data["tags"]:
        tags_by_category[tag["type"]].append(tag["name"])

    return HTMLResponse(TEMPLATE.substitute(
        title=data["long_title"],
        description=build_description(tags_by_category),
        image=(DYNASTY_BASE_URL + data["pages"][0]["url"]),
        location=location,
        extra="",
    ))


@app.get("/images/{slug}")
async def route_dynasty_scans_images(request: Request, slug: str):
    location = f"{DYNASTY_BASE_URL}/images/{slug}?{request.query_params}"
    if not is_bot(request):
        return RedirectResponse(location, status_code=302)

    async with client_session.get(location) as response:
        content = await response.read()

    html = BeautifulSoup(content, features="html.parser")
    image_path = html.find(attrs={"class": "image"}).find("img").attrs["src"]
    tag_links = html.find(attrs={"class": "tags"}).find_all("a")

    all_tag_names = []
    tags_by_category = defaultdict(list)
    for link in tag_links:
        text: str = link.getText()
        if ":" in text:
            kind, name = text.split(":", maxsplit=1)
            kind = kind.strip()
            name = name.strip()
        else:
            kind = "General"
            name = text

        all_tag_names.append(name)
        tags_by_category[kind].append(name)

    return HTMLResponse(TEMPLATE.substitute(
        title=f"Image: {', '.join(all_tag_names)}",
        description=build_description(tags_by_category),
        image=(DYNASTY_BASE_URL + image_path),
        location=location,
        extra=LARGE_IMAGE_TAG,
    ))
