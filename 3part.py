#3.1 Loading both files and looking at the data.
pay = pd.read_csv('actors_pay.csv')
films = pd.read_csv('actors_films.csv')

print(films.shape)
print(films.dtypes)
display(films.head())
print(films.isna().sum())
print(pay.shape)
print(pay.dtypes)
display(pay.head())
print(pay.isna().sum(), "\n")
print(pay.value_counts('Type'))
mask = pay['Actor'].str.contains('n/a', case = False)
display(pay[mask])
print(mask.sum())

#3.2 Cleaning the pay table. We remove 8 rows where the actress is "N/a" and the pay is empty, add the column Pay_m (pay in millions) and compare the two types of pay.
print("before removing rows with n/a in actors: ", pay.shape)
pay = pay[~mask]
print("after: ", pay.shape)
display(pay.isna().sum())
pay['Pay_m'] = pay['Pay'] / 1000000
pay.groupby("Type")["Pay_m"].describe()

#3.3 Looking at the films table. We change Release_Date from text to a date, add the column Year and look for strange values in rating, votes and box office.
films['Release_Date'] = pd.to_datetime(films['Release_Date'])
films['Year'] = films['Release_Date'].dt.year
print(films.dtypes)


display(films[["Rating", "Vote_Count", "Box_Office"]].describe())
display(films[["Actor", "Movie", "Year", "Vote_Count", "Box_Office"]].sort_values('Vote_Count').head(15))
display(films[["Actor", "Movie", "Year", "Vote_Count", "Box_Office"]].sort_values('Box_Office').head(15))

print("\nfilms with a box office of less than 100,000: ", (films['Box_Office'] < 100000).sum())
print("\nfilms with a box office of less than 1,000,000: ", (films['Box_Office'] < 1000000).sum())
print("\nfilms with a vote count of less than 10: ", (films['Vote_Count'] < 10).sum())
print("\nfilms with a vote count of less than 50: ", (films['Vote_Count'] < 50).sum())

#3.4 Cleaning the films table. We keep only films with box office of at least 100,000 dollars and at least 50 votes, add the column Box_Office_m (box office in millions) and check duplicates and the number of films per actor.
keep = (films['Box_Office'] >= 100000) & (films['Vote_Count'] >= 50)
print(len(films), "->", keep.sum())
films = films[keep]

films['Box_Office_m'] = films['Box_Office'] / 1000000

print(films.duplicated(subset=['Actor', 'Movie_ID']).sum())
print(films['Actor'].value_counts().tail(10))
print(films["Actor"].nunique())

#3.5 Making one row per actor. We group the films by actor and calculate the number of films, the average rating and the average and median box office. We do the same for pay: the number of pay records, the average pay and the maximum pay.
film_stats = films.groupby("Actor").agg(
    Films_Count=("Movie", "count"),
    Avg_Rating=("Rating", "mean"),
    Median_Box_Office_m=("Box_Office_m", "median"),
    Avg_Box_Office_m=("Box_Office_m", "mean"),
).round(2).reset_index()

display(film_stats.head())pay_stats = pay.groupby("Actor").agg(
    Pay_Records=("Pay_m", "count"),
    Avg_Pay_m=("Pay_m", "mean"),
    Max_Pay_m=("Pay_m", "max"),
).round(2).reset_index()

display(pay_stats.head())

#3.6 Merging the two sources. We check that the actor names are the same in both tables and join pay_stats with film_stats by the column Actor. In the result one row is one actor.
check = pd.merge(film_stats, pay_stats, on="Actor", how="outer", indicator=True)
display(check.head())
print(check["_merge"].value_counts())

actor_summary = pd.merge(film_stats, pay_stats, on="Actor", how="inner")
display(actor_summary.head())

print(actor_summary.shape)
print(actor_summary.isna().sum())
display(actor_summary.sort_values('Max_Pay_m', ascending=False).head(10))

#3.7 Merging pay for a single film with the data of the same film. We take the per_film rows from the pay table and join them with the films table by two columns: actor and film title. Then we check which rows did not find a pair.
pay_film = pay[pay['Type'] == "per_film"].copy()
print(len(pay_film))

film_merge = pd.merge(pay_film, films[["Actor", "Movie", "Release_Date", "Rating", "Vote_Count", "Box_Office_m"]],
             left_on=["Actor", "Film"], right_on=["Actor", "Movie"],
             how="left", indicator=True)

display(film_merge.head())
print(film_merge["_merge"].value_counts())
display(film_merge[film_merge["_merge"] == "left_only"][["Actor", "Film", "Year"]])

#3.8 Fixing the film titles. We look for the four films without a pair in the films table. If the title is written differently in Wikipedia and TMDB, we change it and merge again. If the film is not in the films table, we leave the row without a pair.
found = films[(films["Actor"] == "Keanu Reeves") & (films["Movie"].str.contains("Matrix", case=False))]
display(found[["Actor", "Movie", "Release_Date"]])
found = films[(films["Actor"] == "Tom Cruise") & (films["Movie"].str.contains("Impossible", case=False))]
display(found[["Actor", "Movie", "Release_Date"]])
found = films[(films["Actor"] == "Allu Arjun") & (films["Movie"].str.contains("Pushpa", case=False))]
display(found[["Actor", "Movie", "Release_Date"]])
found = films[(films["Actor"] == "Will Smith") & (films["Movie"].str.contains("Emancipation", case=False))]
display(found[["Actor", "Movie", "Release_Date"]])

pay_film["Film"] = pay_film["Film"] .replace({"Mission: Impossible 2": "Mission: Impossible II", "Pushpa 2: The Rule": "Pushpa 2 - The Rule"})
film_merge = pd.merge(pay_film, films[["Actor", "Movie", "Release_Date", "Rating", "Vote_Count", "Box_Office_m"]],
             left_on=["Actor", "Film"], right_on=["Actor", "Movie"],
             how="left", indicator=True)

display(film_merge.head())
print(film_merge["_merge"].value_counts())
display(film_merge[film_merge["_merge"] == "left_only"][["Actor", "Film", "Year"]])

#3.9 Saving the results. For the film table we keep only the rows that found a pair and only the columns we need. Then we check both final tables and save them to CSV files for the analysis part.
film_pay = film_merge[film_merge["_merge"] == "both"]
film_pay = film_pay[['Actor', 'Film', 'Year', 'Pay_m', 'Rating', 'Vote_Count', 'Box_Office_m']]

print("shape of first table: ", actor_summary.shape)
display(actor_summary.isna().sum())

print("\nshape of second table: ",film_pay.shape)
display(film_pay.isna().sum())

actor_summary.to_csv("actor_summary.csv", index=False)
film_pay.to_csv("film_pay.csv", index=False)

print("\n", pd.read_csv("actor_summary.csv").shape)
print("\n", pd.read_csv("film_pay.csv").shape)
