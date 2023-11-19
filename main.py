from collections import defaultdict
from string import Template

import aiohttp
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse, HTMLResponse

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
    <meta property="og:site_name" content="Dynasty Scans Embedded"/>
    <meta property="og:description" content="$description"/>
    <meta property="og:image" content="$image"/>
    <meta property="og:url" content="$location"/>
</head>
<body>
</body>
</html>
""")


@app.get("/chapters/{slug}")
async def route_dynasty_scans_chapters(request: Request, slug: str):
    base_url = "https://dynasty-scans.com"
    location = f"{base_url}/chapters/{slug}"
    if "BOT" not in request.headers.get("User-Agent", "").upper():
        return RedirectResponse(
            location,
            status_code=302,
        )

    url = f"{base_url}/chapters/{slug}.json"
    async with client_session.get(url) as response:
        data = await response.json()

    tags_by_category = defaultdict(list)
    for tag in data["tags"]:
        tags_by_category[tag["type"]].append(tag["name"])

    description = []
    if tags_by_category["Doujin"]:
        description.append(f"{' and '.join(tags_by_category['Doujin'])} Doujin.")
    if tags_by_category["General"]:
        description.append(f"Tags: {', '.join(tags_by_category['General'])}.")
    if tags_by_category["Author"]:
        description.append(f"By {' and '.join(tags_by_category['Author'])}.")
    if tags_by_category["Scanlator"]:
        description.append(f"Scanned by {' and '.join(tags_by_category['Scanlator'])}.")

    return HTMLResponse(TEMPLATE.substitute(
        title=data["long_title"],
        description=" ".join(description),
        image=(base_url + data["pages"][0]["url"]),
        location=location,
    ))
