#1.1 mport the libraries we need (requests, pandas, BeautifulSoup, robotparser) and set the page URL and a User-Agent header for our requests.
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

URL = "https://en.wikipedia.org/wiki/List_of_highest-paid_film_actors"
HEADERS = {"User-Agent": "SIS student project (your_email@example.com)"}

#1.2 Downloading Wikipedia's robots.txt and use RobotFileParser to check that scraping this page is allowed.
robots = requests.get("https://en.wikipedia.org/robots.txt", headers=HEADERS)
rp = RobotFileParser()
rp.parse(robots.text.splitlines())

print("robots.txt status:", robots.status_code)
print("Can we scrape this page?", rp.can_fetch("*", URL))
# Wikipedia allows /wiki/ pages for normal crawlers.
# We send only one request for the page, so we don't overload the server.

#1.3 Downloading the page, remove footnotes like [1], find all tables with the class wikitable and print their headers.
response = requests.get(URL, headers=HEADERS)
print("Page status:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

for sup in soup.find_all("sup"):
    sup.decompose()

tables = soup.find_all("table", class_="wikitable")
print("Number of tables:", len(tables))
for i, t in enumerate(tables):
    header = [th.get_text(" ", strip=True) for th in t.find("tr").find_all("th")]
    print(i, header)

#1.4 The function read_table goes through the table rows and fills in cells merged with rowspan, so the columns don't shift.
def read_table(table):
    rows = []
    waiting = {}

    for tr in table.find_all("tr"):
        if not tr.find("td"):
            continue
        cells = tr.find_all(["td", "th"])
        row = []
        col = 0
        i = 0
        while i < len(cells) or col in waiting:
            if col in waiting:
                text, left = waiting[col]
                row.append(text)
                if left == 1:
                    del waiting[col]
                else:
                    waiting[col] = [text, left - 1]
            else:
                cell = cells[i]
                i += 1
                text = cell.get_text(" ", strip=True)
                span = int(cell.get("rowspan", 1))
                if span > 1:
                    waiting[col] = [text, span - 1]
                row.append(text)
            col += 1
        rows.append(row)
    return rows

#1.5 Using the column headers, we find the two tables we need: pay for a single film and the highest-paid actor and actress of each year.
film_table = None    # Actor | Film | Year | Salary | Total income | Ref.
annual_table = None  # Year | Actor | Earnings | Actress | Earnings | Ref.

for t in tables:
    header = " ".join(th.get_text(" ", strip=True) for th in t.find("tr").find_all("th"))
    if "Film" in header and "Salary" in header:
        film_table = t
    elif "Actress" in header:
        annual_table = t

print(film_table is not None, annual_table is not None)

#1.6 Turn the first table into a DataFrame with the columns Actor, Film, Year, Salary and Total income, and mark its rows as per_film.
rows1 = read_table(film_table)
df_film = pd.DataFrame(
    [r[:5] for r in rows1],
    columns=["Actor", "Film", "Year", "Salary_raw", "Total_income_raw"],
)
df_film["Type"] = "per_film"
df_film.head(10)

#1.7 Parse the second table, split each row with an actor and an actress into two separate rows, and mark them as annual.
rows2 = read_table(annual_table)
annual = []
for r in rows2:
    if len(r) < 5:
        print("skipped row:", r)
        continue
    year = r[0]
    annual.append({"Actor": r[1], "Year": year, "Pay_raw": r[2]})
    annual.append({"Actor": r[3], "Year": year, "Pay_raw": r[4]})

df_annual = pd.DataFrame(annual)
df_annual["Type"] = "annual"
df_annual.head(10)

#1.8 The function money_to_number converts text like "$75 million" or "$30,000,000" into numbers we can calculate with.
def money_to_number(text):
    if not isinstance(text, str) or text.strip() in ("", "—", "-", "N/A"):
        return None
    t = text.lower().replace(",", "")
    nums = re.findall(r"\d+(?:\.\d+)?", t)
    if not nums:
        return None
    value = float(nums[0])
    if "billion" in t:
        value *= 1_000_000_000
    elif "million" in t:
        value *= 1_000_000
    return value


df_film["Pay_raw"] = df_film["Total_income_raw"]
df_film["Pay"] = df_film["Pay_raw"].apply(money_to_number)
df_film["Salary"] = df_film["Salary_raw"].apply(money_to_number)
df_annual["Pay"] = df_annual["Pay_raw"].apply(money_to_number)


#1.9 Combinig both tables, clean the names and years, remove empty rows and duplicates, and check how many values are missing.
pay = pd.concat([df_film, df_annual], ignore_index=True)

pay["Actor"] = pay["Actor"].str.strip()
pay["Year"] = pay["Year"].str.extract(r"(\d{4})")[0].astype("Int64")
pay = pay[pay["Actor"] != ""]
pay = pay.drop_duplicates()

pay = pay[["Actor", "Film", "Year", "Pay", "Pay_raw", "Salary", "Type"]]
print(pay.shape)
print(pay.isna().sum())
pay.head(20)

#1.10 Saving the result to actors_pay.csv and print the list of unique actors for the API part.
pay.to_csv("actors_pay.csv", index=False)

actors = sorted(pay["Actor"].unique())
print("Unique actors:", len(actors))
print(actors)

