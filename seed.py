"""Load starter films into the database. Safe to run more than once.

Each film is upserted by title. Poster image and a short synopsis are fetched
once from Wikipedia's public REST API (no key needed) and stored on the film
document, so the app never calls an external service at request time. If a
fetch fails the film is still seeded, just without a poster.
"""
import json
import os
import re
import urllib.parse
import urllib.request

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("MONGO_DBNAME", "filmreviews")]

# (title, year, director, genre, wikipedia page title)
FILMS = [
    ("The Godfather", 1972, "Francis Ford Coppola", "Crime", "The Godfather"),
    ("Pulp Fiction", 1994, "Quentin Tarantino", "Crime", "Pulp Fiction"),
    ("Spirited Away", 2001, "Hayao Miyazaki", "Animation", "Spirited Away"),
    ("The Dark Knight", 2008, "Christopher Nolan", "Action", "The Dark Knight"),
    ("Parasite", 2019, "Bong Joon-ho", "Thriller", "Parasite (2019 film)"),
    ("Get Out", 2017, "Jordan Peele", "Horror", "Get Out"),
    ("Moonlight", 2016, "Barry Jenkins", "Drama", "Moonlight (2016 film)"),
    ("Inception", 2010, "Christopher Nolan", "Sci-Fi", "Inception"),
    ("Everything Everywhere All at Once", 2022, "Daniels", "Sci-Fi", "Everything Everywhere All at Once"),
    ("La La Land", 2016, "Damien Chazelle", "Musical", "La La Land"),
    ("Mad Max: Fury Road", 2015, "George Miller", "Action", "Mad Max: Fury Road"),
    ("Do the Right Thing", 1989, "Spike Lee", "Drama", "Do the Right Thing"),
    ("Superbad", 2007, "Greg Mottola", "Comedy", "Superbad"),
    ("Arrival", 2016, "Denis Villeneuve", "Sci-Fi", "Arrival (film)"),
    ("Whiplash", 2014, "Damien Chazelle", "Drama", "Whiplash (2014 film)"),
    ("Spider-Man: Into the Spider-Verse", 2018, "Persichetti, Ramsey, Rothman", "Animation", "Spider-Man: Into the Spider-Verse"),
    ("The Shining", 1980, "Stanley Kubrick", "Horror", "The Shining (film)"),
    ("Lady Bird", 2017, "Greta Gerwig", "Comedy", "Lady Bird (film)"),
    ("Oppenheimer", 2023, "Christopher Nolan", "Drama", "Oppenheimer (film)"),
    ("Dune: Part Two", 2024, "Denis Villeneuve", "Sci-Fi", "Dune: Part Two"),
]

WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
HEADERS = {"User-Agent": "ReelTalk/1.0 (NYU software engineering class project)"}


def fetch_wiki(page_title):
    """Return {"poster": url, "synopsis": text} from Wikipedia, or {} on any failure."""
    url = WIKI_SUMMARY + urllib.parse.quote(page_title.replace(" ", "_"), safe="():,")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
    except Exception as exc:  # network down, page missing, bad JSON
        print(f"  (no poster for {page_title}: {exc})")
        return {}
    out = {}
    thumb = (data.get("thumbnail") or {}).get("source")
    if thumb:
        # Wikimedia thumb URLs end in /<width>px-<file>; ask for a sharper 500px version
        out["poster"] = re.sub(r"/\d+px-", "/500px-", thumb)
    extract = (data.get("extract") or "").strip()
    if extract:
        out["synopsis"] = extract
    return out


for title, year, director, genre, wiki in FILMS:
    doc = {"title": title, "year": year, "director": director, "genre": genre}
    doc.update(fetch_wiki(wiki))
    db.films.update_one({"title": title}, {"$set": doc}, upsert=True)

with_posters = db.films.count_documents({"poster": {"$exists": True}})
print(f"Seeded {db.films.count_documents({})} films ({with_posters} with posters).")
