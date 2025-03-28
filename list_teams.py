import pandas as pd

# Load the stats CSV
df = pd.read_csv("dffl_stats.csv")

# Get unique teams
teams = sorted(df["Team"].unique())

print("\nTeams to add to team_info.csv:")
print("=" * 30)
for i, team in enumerate(teams, 1):
    print(f"{i}. {team}")

print("\nTotal teams:", len(teams)) 