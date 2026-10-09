# Highest-Paid Film Actors: Pay vs Rating and Box Office

A student data project that checks whether the highest-paid film actors also make the best-rated and most commercially successful films.

Pay data is scraped from Wikipedia, film data comes from the TMDB API, and the two sources are cleaned, merged and analysed with correlation tests and graphs.

## Research question

Is there a relationship between how much an actor is paid and:
- the average TMDB rating of their films?
- the average box office of their films?

## Project structure

| Part | What it does | Input | Output |
|------|--------------|-------|--------|
| 1. Web scraping | Scrapes two tables from Wikipedia: pay for a single film and the highest-paid actor/actress of each year | Wikipedia page | `actors_pay.csv` |
| 2. API | Finds each actor in TMDB and downloads their films with rating, votes and box office | `actors_pay.csv`, TMDB API | `actors_films.csv` |
| 3. Cleaning and merging | Cleans both tables, makes one row per actor and links per-film pay with the same film's data | `actors_pay.csv`, `actors_films.csv` | `actor_summary.csv`, `film_pay.csv` |
| 4. Analysis | Descriptive statistics, correlation matrix, Pearson and Spearman tests, three graphs | `actor_summary.csv` | `graph1–3_*.png` |

## Data sources

- **Wikipedia** – [List of highest-paid film actors](https://en.wikipedia.org/wiki/List_of_highest-paid_film_actors)
- **TMDB API** – [The Movie Database](https://www.themoviedb.org/) (`/search/person`, `/person/{id}/movie_credits`, `/movie/{id}`)

## Requirements

- Python 3.9+
- Libraries: `requests`, `pandas`, `beautifulsoup4`, `matplotlib`, `seaborn`, `scipy`, `python-dotenv` (only when running locally)

```bash
pip install requests pandas beautifulsoup4 matplotlib seaborn scipy python-dotenv
```

## How to run

1. **Get a TMDB API key** at https://www.themoviedb.org/settings/api.
2. **Store the key outside the code:**
   - In Google Colab: add a secret called `TMDB_API_KEY` (key icon in the left panel).
   - Locally: create a `.env` file next to the notebook:
     ```
     TMDB_API_KEY=your_key_here
     ```
     and add `.env` to `.gitignore`.
3. In Part 1, replace `your_email@example.com` in the `User-Agent` header with your own contact email.
4. Run the parts in order: 1 → 2 → 3 → 4. Each part reads the CSV files saved by the previous one. The main loop in Part 2 (cell 2.8) takes several minutes.

## Method

### Part 1- Web scraping
- Checks `robots.txt` with `RobotFileParser` before scraping; the page is downloaded with a single request.
- Removes footnote markers like `[1]`.
- `read_table()` handles cells merged with `rowspan`, so columns don't shift.
- The two needed tables are found by their headers, not by position.
- Each annual row (actor + actress) is split into two rows. Rows are marked `per_film` or `annual` in the `Type` column.
- `money_to_number()` turns text like `"$75 million"` or `"$30,000,000"` into numbers.

### Part 2- TMDB API
- `tmdb_get()` retries up to 3 times on network errors and on status 429 (rate limit).
- Actors are matched by name, preferring results with `known_for_department == "Acting"`. Wikipedia and TMDB names are shown side by side to check the match.
- Roles are filtered out if they are voice roles, cameos, uncredited, self or archive footage; documentaries and animation; cast order 10 or lower in billing; unreleased or with no votes.
- Film details are cached so the same film is never requested twice.
- Final filter: only released films with rating, votes and box office above 0.

### Part 3- Cleaning and merging
- Removes 8 pay rows where the actress was `N/a` with no pay.
- Keeps films with box office of at least $100,000 and at least 50 votes, to remove incomplete TMDB records.
- Converts pay and box office to millions (`Pay_m`, `Box_Office_m`).
- `actor_summary.csv` – one row per actor: number of films, average rating, average and median box office, number of pay records, average and maximum pay.
- `film_pay.csv` – per-film pay joined with the same film's data by actor and title. Titles written differently in the two sources were fixed manually (e.g. *Mission: Impossible 2* → *Mission: Impossible II*, *Pushpa 2: The Rule* → *Pushpa 2 - The Rule*); films missing from the TMDB table stay unmatched.

### Part 4- Analysis
- Pay is measured as `Avg_Pay_m` – the actor's average pay over all their Wikipedia records.
- Descriptive statistics (min, max, mean, median, std, range) and the actors with the highest and lowest values.
- Pearson correlation matrix of all numeric columns.
- Pay vs rating and pay vs box office: Pearson r with p-value, and Spearman correlation, which is less affected by a few very highly paid actors. Median box office is also tested, since one blockbuster can move the average a lot.

## Output files

| File | Description |
|------|-------------|
| `actors_pay.csv` | All pay records from Wikipedia (per-film and annual) |
| `actors_films.csv` | Actors' films from TMDB after filtering |
| `actor_summary.csv` | One row per actor with film and pay statistics |
| `film_pay.csv` | Per-film pay matched with that film's rating and box office |
| `graph1_pay_vs_rating.png` | Scatter plot: pay vs average rating, with trend line |
| `graph2_pay_vs_box_office.png` | Scatter plot: pay vs average box office, with trend line |
| `graph3_top10_pay.png` | Bar chart: top 10 actors by average pay |


