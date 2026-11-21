import json
import time
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

USER = "AndersonRamon"


def tempo_atras(ts):
    s = max(0, int(time.time()) - ts)
    for nome, seg in (
        ("year", 31536000),
        ("month", 2592000),
        ("week", 604800),
        ("day", 86400),
        ("hour", 3600),
        ("minute", 60),
    ):
        n = s // seg
        if n >= 1:
            return f"{n} {nome}{'s' if n > 1 else ''} ago"
    return "just now"


def anilist(query, variables):
    req = urllib.request.Request(
        "https://graphql.anilist.co",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "anilist-widget",
        },
    )
    with urllib.request.urlopen(req) as r:
        j = json.load(r)
    if "errors" in j:
        raise Exception(j["errors"][0]["message"])
    return j["data"]


u = anilist(
    """query ($name: String) {
      User(name: $name) {
        id
        name
        avatar { medium }
        statistics {
          anime { count episodesWatched minutesWatched }
          manga { count volumesRead chaptersRead }
        }
      }
    }""",
    {"name": USER},
)["User"]

acts = anilist(
    """query ($id: Int) {
      Page(page: 1, perPage: 1) {
        activities(userId: $id, type: MEDIA_LIST, sort: ID_DESC) {
          ... on ListActivity {
            status
            progress
            createdAt
            media { title { romaji } coverImage { extraLarge } }
          }
        }
      }
    }""",
    {"id": u["id"]},
)["Page"]["activities"]

last_activity = "-"
last_image = ""
last_seen = "Last Activity: -"
if acts:
    a = acts[0]
    status = a["status"][:1].upper() + a["status"][1:]
    prog = f" {a['progress']} of" if a.get("progress") else ""
    last_activity = f"{status}{prog} {a['media']['title']['romaji']}"
    last_image = a["media"]["coverImage"]["extraLarge"]
    last_seen = f"Last Activity: {tempo_atras(a['createdAt'])}"

agora = datetime.now(ZoneInfo("America/Fortaleza")).strftime("%d/%m/%Y %H:%M:%S")
anime = u["statistics"]["anime"]
manga = u["statistics"]["manga"]

body = {
    "username": u["name"],
    "avatar_url": u["avatar"]["medium"],
    "total_anime": anime["count"],
    "episodes_watched": anime["episodesWatched"],
    "days_watched": round(anime["minutesWatched"] / 1440),
    "total_manga": manga["count"],
    "volumes_read": manga["volumesRead"],
    "chapters_read": manga["chaptersRead"],
    "last_activity": last_activity,
    "last_activity_image": last_image,
    "last_updated": f"Última atualização: {agora}",
    "last_seen": last_seen,
}

with open("anilist.json", "w", encoding="utf-8") as f:
    json.dump(body, f, ensure_ascii=False, indent=2)
