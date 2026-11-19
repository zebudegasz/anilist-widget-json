import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

USER = "AndersonRamon"


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
            media { title { romaji } coverImage { medium } }
          }
        }
      }
    }""",
    {"id": u["id"]},
)["Page"]["activities"]

last_activity = "Last Activity: -"
last_image = ""
if acts:
    a = acts[0]
    status = a["status"][:1].upper() + a["status"][1:]
    prog = f" {a['progress']} of" if a.get("progress") else ""
    last_activity = f"Last Activity: {status}{prog} {a['media']['title']['romaji']}"
    last_image = a["media"]["coverImage"]["medium"]

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
}

with open("anilist.json", "w", encoding="utf-8") as f:
    json.dump(body, f, ensure_ascii=False, indent=2)
