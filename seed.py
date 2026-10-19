"""Load starter films into the database. Safe to run more than once."""
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("MONGO_DBNAME", "filmreviews")]

FILMS = [
    ("The Godfather", 1972, "Francis Ford Coppola", "Crime"),
    ("Pulp Fiction", 1994, "Quentin Tarantino", "Crime"),
    ("Spirited Away", 2001, "Hayao Miyazaki", "Animation"),
    ("The Dark Knight", 2008, "Christopher Nolan", "Action"),
    ("Parasite", 2019, "Bong Joon-ho", "Thriller"),
    ("Get Out", 2017, "Jordan Peele", "Horror"),
    ("Moonlight", 2016, "Barry Jenkins", "Drama"),
    ("Inception", 2010, "Christopher Nolan", "Sci-Fi"),
    ("Everything Everywhere All at Once", 2022, "Daniels", "Sci-Fi"),
    ("La La Land", 2016, "Damien Chazelle", "Musical"),
    ("Mad Max: Fury Road", 2015, "George Miller", "Action"),
    ("Do the Right Thing", 1989, "Spike Lee", "Drama"),
    ("Superbad", 2007, "Greg Mottola", "Comedy"),
    ("Arrival", 2016, "Denis Villeneuve", "Sci-Fi"),
    ("Whiplash", 2014, "Damien Chazelle", "Drama"),
    ("Spider-Man: Into the Spider-Verse", 2018, "Persichetti, Ramsey, Rothman", "Animation"),
    ("The Shining", 1980, "Stanley Kubrick", "Horror"),
    ("Lady Bird", 2017, "Greta Gerwig", "Comedy"),
    ("Oppenheimer", 2023, "Christopher Nolan", "Drama"),
    ("Dune: Part Two", 2024, "Denis Villeneuve", "Sci-Fi"),
]

for title, year, director, genre in FILMS:
    db.films.update_one(
        {"title": title},
        {"$set": {"title": title, "year": year, "director": director, "genre": genre}},
        upsert=True,
    )

print(f"Seeded {db.films.count_documents({})} films.")
