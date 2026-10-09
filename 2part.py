#**2.1** Import the libraries such as os, time, requests, pandas and set the TMDB base URL, the file names and the settings for our filters
import os
import time
import requests
import pandas as pd

BASE_URL = "https://api.themoviedb.org/3"
PAY_FILE = "actors_pay.csv"
OUT_FILE = "actors_films.csv"

DOCUMENTARY = 99
ANIMATION = 16
MAX_CAST_ORDER = 10
SKIP_WORDS = ["voice", "cameo", "uncredited", "self", "archive"]

#2.2 Reading the API key from Colab Secrets or .env, so the key is never written in the notebook
try:
    from google.colab import userdata
    API_KEY = userdata.get("TMDB_API_KEY")
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("TMDB_API_KEY")

print("Key loaded:", bool(API_KEY))

#2.3 The function tmdb_get sends one GET request to TMDB, adds the API key, checks the status code and returns the JSON answer as a Python dictionary
session = requests.Session()

def tmdb_get(path, **params):
    params["api_key"] = API_KEY
    for attempt in range(3):
        try:
            r = session.get(BASE_URL + path, params=params, timeout=15)
        except requests.RequestException:
            time.sleep(2)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(2)
            continue
        print("Request failed:", path, "status:", r.status_code)
        return None
    print("Request failed after 3 tries:", path)
    return None


test = tmdb_get("/search/person", query="Tom Cruise")
print("Test request works:", test is not None)

#2.4 Loading actors_pay.csv from Part 1 and make the list of unique actors, without the empty value as — N/a
pay = pd.read_csv(PAY_FILE)

actors = sorted(pay["Actor"].dropna().unique())
actors = [a for a in actors if "n/a" not in a.lower()]

print("Actors from Part 1:", len(actors))
print(actors)

#2.5 For each actor we search TMDB by name and save the id of the person. We keep the name from Wikipedia and the name from TMDB side by side to check the match.
def find_actor(name):
    data = tmdb_get("/search/person", query=name)
    if not data or not data["results"]:
        return None
    for person in data["results"]:
        if person.get("known_for_department") == "Acting":
            return person
    return data["results"][0]


id_rows = []
not_found = []
for name in actors:
    person = find_actor(name)
    if person is None:
        not_found.append(name)
        continue
    id_rows.append({
        "Actor": name,
        "TMDB_ID": person["id"],
        "TMDB_Name": person["name"],
    })

df_ids = pd.DataFrame(id_rows)
print("Found:", len(df_ids), "| Not found:", not_found)
print("Names that are different in TMDB:")
print(df_ids[df_ids["Actor"] != df_ids["TMDB_Name"]])
df_ids.head(10)

#2.6 The function get_roles downloads the list of films of one actor and removes voice roles, cameos, documentaries, animation and films that are not released or have no votes.
def get_roles(person_id):
    data = tmdb_get(f"/person/{person_id}/movie_credits")
    if not data:
        return []
    roles = []
    for c in data["cast"]:
        character = (c.get("character") or "").lower()
        genres = c.get("genre_ids", [])

        if any(word in character for word in SKIP_WORDS):
            continue
        if DOCUMENTARY in genres or ANIMATION in genres:
            continue
        if c.get("order", 999) >= MAX_CAST_ORDER:
            continue
        if not c.get("release_date"):
            continue
        if c.get("vote_count", 0) == 0:
            continue

        roles.append({
            "Movie_ID": c["id"],
            "Character": c.get("character"),
            "Cast_Order": c.get("order"),
        })
    return roles


example = get_roles(df_ids.loc[0, "TMDB_ID"])
print(df_ids.loc[0, "Actor"], "- roles after the first filter:", len(example))
print(example[:3])

#2.7 The function get_movie downloads the details of one film (title, date, rating, votes, revenue). We save every answer in a dictionary, so the same film is never requested twice
movie_cache = {}

def get_movie(movie_id):
    if movie_id not in movie_cache:
        movie_cache[movie_id] = tmdb_get(f"/movie/{movie_id}")
        time.sleep(0.05)
    return movie_cache[movie_id]


m = get_movie(example[0]["Movie_ID"])
print(m["title"], "|", m["release_date"], "|", m["vote_average"], "|", m["vote_count"], "|", m["revenue"])

#2.8 Main loop: for each actor we take the roles, download the details of each film and add one row (actor + film) to the table. This cell runs for several minutes
rows = []
for _, a in df_ids.iterrows():
    roles = get_roles(a["TMDB_ID"])
    for role in roles:
        m = get_movie(role["Movie_ID"])
        if not m:
            continue
        rows.append({
            "Actor": a["Actor"],
            "TMDB_ID": a["TMDB_ID"],
            "Movie_ID": m["id"],
            "Movie": m.get("title"),
            "Release_Date": m.get("release_date"),
            "Rating": m.get("vote_average"),
            "Vote_Count": m.get("vote_count"),
            "Box_Office": m.get("revenue"),
            "Status": m.get("status"),
            "Character": role["Character"],
            "Cast_Order": role["Cast_Order"],
        })
    print(a["Actor"], "-", len(roles), "films")

df_raw = pd.DataFrame(rows)
print("Rows before the final filter:", df_raw.shape)
print("Requests saved by the cache:", len(df_raw) - len(movie_cache))

#2.9 Final filter: we keep only released films with rating, votes and box office greater than 0, remove duplicates and fix the data types
films = df_raw[
    (df_raw["Status"] == "Released")
    & (df_raw["Rating"] > 0)
    & (df_raw["Vote_Count"] > 0)
    & (df_raw["Box_Office"] > 0)
].copy()

films = films.drop_duplicates(subset=["Actor", "Movie_ID"])
films["Release_Date"] = pd.to_datetime(films["Release_Date"], errors="coerce")
films = films.sort_values(["Actor", "Release_Date"]).reset_index(drop=True)

films = films[["Actor", "Movie", "Release_Date", "Rating", "Vote_Count", "Box_Office",
               "Character", "Cast_Order", "TMDB_ID", "Movie_ID"]]

print("Before:", len(df_raw), "| After:", len(films))
print(films.isna().sum())
films.head(10)

#2.10 Saving the result to actors_films.csv and check how many films each actor has and which actors have no films after the filter
films.to_csv(OUT_FILE, index=False)

per_actor = films.groupby("Actor")["Movie"].count().sort_values()
print("Rows:", len(films), "| Actors:", films["Actor"].nunique())
print("Actors with no films after the filter:", sorted(set(actors) - set(films["Actor"])))
print(per_actor.head(10))

