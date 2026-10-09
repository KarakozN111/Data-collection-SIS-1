#4.1 Loading the final table from Part 3 (one row is one actor) and looking at the data. As Pay we use Avg_Pay_m: the average pay of the actor in millions of dollars over all his records in the Wikipedia tables.
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

df = pd.read_csv("actor_summary.csv")

print("Rows and columns:", df.shape)
print(df.dtypes)
display(df.head())

print("Missing values in each column:")
print(df.isna().sum())

# we need pay, rating and box office for every actor, so rows without them are removed
before = len(df)
df = df.dropna(subset=["Avg_Pay_m", "Avg_Rating", "Avg_Box_Office_m"])
print("Actors before:", before, "| Actors after:", len(df))

#4.2 Descriptive statistics. For pay, rating and box office we calculate min, max, mean, median and the spread (standard deviation and range). Then we look which actors have the highest and the lowest values.
cols = ["Avg_Pay_m", "Max_Pay_m", "Avg_Rating", "Avg_Box_Office_m", "Median_Box_Office_m", "Films_Count"]

stats = df[cols].describe().T
stats["range"] = stats["max"] - stats["min"]
stats = stats.rename(columns={"50%": "median"})
display(stats[["count", "min", "max", "mean", "median", "std", "range"]].round(2))

# actors with the highest and the lowest values
top_pay = df.loc[df["Avg_Pay_m"].idxmax()]
low_pay = df.loc[df["Avg_Pay_m"].idxmin()]
top_rating = df.loc[df["Avg_Rating"].idxmax()]
low_rating = df.loc[df["Avg_Rating"].idxmin()]
top_box = df.loc[df["Avg_Box_Office_m"].idxmax()]
low_box = df.loc[df["Avg_Box_Office_m"].idxmin()]

print("Highest average pay:", top_pay["Actor"], "-", top_pay["Avg_Pay_m"], "million $")
print("Lowest average pay:", low_pay["Actor"], "-", low_pay["Avg_Pay_m"], "million $")
print("Highest average rating:", top_rating["Actor"], "-", top_rating["Avg_Rating"])
print("Lowest average rating:", low_rating["Actor"], "-", low_rating["Avg_Rating"])
print("Highest average box office:", top_box["Actor"], "-", top_box["Avg_Box_Office_m"], "million $")
print("Lowest average box office:", low_box["Actor"], "-", low_box["Avg_Box_Office_m"], "million $")

#4.3 Correlation matrix. We calculate the Pearson correlation between all numeric columns. The value is from -1 to 1: close to 0 means no linear relationship, close to 1 or -1 means a strong one.
corr = df[cols].corr().round(2)
display(corr)

print("Correlation of Avg_Pay_m with the other columns:")
print(corr["Avg_Pay_m"].drop("Avg_Pay_m").sort_values(ascending=False))

#4.4 Pay and Average Rating. We calculate the Pearson correlation with its p-value and the Spearman correlation. Spearman uses ranks, so a few actors with very high pay do not change it so much. The function strength turns the number into words.
def strength(r):
    r = abs(r)
    if r < 0.2:
        return "very weak or no"
    elif r < 0.4:
        return "weak"
    elif r < 0.6:
        return "moderate"
    else:
        return "strong"


r_rating, p_rating = pearsonr(df["Avg_Pay_m"], df["Avg_Rating"])
s_rating = df["Avg_Pay_m"].corr(df["Avg_Rating"], method="spearman")

print("Number of actors:", len(df))
print("Pearson correlation (Pay and Average Rating):", round(r_rating, 3))
print("p-value:", round(p_rating, 4))
print("Spearman correlation (Pay and Average Rating):", round(s_rating, 3))
print("Strength of the relationship:", strength(r_rating))
print("Direction:", "positive" if r_rating > 0 else "negative")
print("Statistically significant (p < 0.05):", p_rating < 0.05)

#4.5 Pay and Average Box Office. The same calculation for the box office. We also check the median box office, because one blockbuster can change the average a lot.
r_box, p_box = pearsonr(df["Avg_Pay_m"], df["Avg_Box_Office_m"])
s_box = df["Avg_Pay_m"].corr(df["Avg_Box_Office_m"], method="spearman")

print("Pearson correlation (Pay and Average Box Office):", round(r_box, 3))
print("p-value:", round(p_box, 4))
print("Spearman correlation (Pay and Average Box Office):", round(s_box, 3))
print("Strength of the relationship:", strength(r_box))
print("Direction:", "positive" if r_box > 0 else "negative")
print("Statistically significant (p < 0.05):", p_box < 0.05)

r_med, p_med = pearsonr(df["Avg_Pay_m"], df["Median_Box_Office_m"])
print("Pearson correlation (Pay and Median Box Office):", round(r_med, 3))
print("p-value:", round(p_med, 4))

#4.6 Graph 1: Pay vs Average Rating. One point is one actor, the line shows the trend. The three actors with the highest pay are signed.
top3 = df.sort_values("Avg_Pay_m", ascending=False).head(3)

plt.figure(figsize=(9, 6))
sns.regplot(data=df, x="Avg_Pay_m", y="Avg_Rating", ci=None,
            scatter_kws={"s": 50, "alpha": 0.8}, line_kws={"color": "gray", "linewidth": 2})

for _, row in top3.iterrows():
    plt.annotate(row["Actor"], (row["Avg_Pay_m"], row["Avg_Rating"]),
                 xytext=(-7, 7), textcoords="offset points", ha="right", fontsize=9,
                 bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1})

plt.title("Pay vs Average Rating (r = " + str(round(r_rating, 2)) + ")")
plt.xlabel("Average pay, million $")
plt.ylabel("Average TMDB rating of the actor's films")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("graph1_pay_vs_rating.png", dpi=150)
plt.show()

#4.7 Graph 2: Pay vs Average Box Office. The same type of graph for the box office.
plt.figure(figsize=(9, 6))
sns.regplot(data=df, x="Avg_Pay_m", y="Avg_Box_Office_m", ci=None,
            scatter_kws={"s": 50, "alpha": 0.8}, line_kws={"color": "gray", "linewidth": 2})

for _, row in top3.iterrows():
    plt.annotate(row["Actor"], (row["Avg_Pay_m"], row["Avg_Box_Office_m"]),
                 xytext=(-7, 7), textcoords="offset points", ha="right", fontsize=9,
                 bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1})

plt.title("Pay vs Average Box Office (r = " + str(round(r_box, 2)) + ")")
plt.xlabel("Average pay, million $")
plt.ylabel("Average box office of the actor's films, million $")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("graph2_pay_vs_box_office.png", dpi=150)
plt.show()

#4.8 Graph 3: Top 10 actors by Pay. A bar chart of the ten actors with the highest average pay.
top10 = df.sort_values("Avg_Pay_m", ascending=False).head(10)
display(top10[["Actor", "Avg_Pay_m", "Avg_Rating", "Avg_Box_Office_m"]])

plt.figure(figsize=(9, 6))
sns.barplot(data=top10, x="Avg_Pay_m", y="Actor", color="steelblue")

plt.title("Top 10 actors by average pay")
plt.xlabel("Average pay, million $")
plt.ylabel("Actor")
plt.grid(axis="x", alpha=0.3)
plt.gca().set_axisbelow(True)
plt.tight_layout()
plt.savefig("graph3_top10_pay.png", dpi=150)
plt.show()

