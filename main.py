import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("Flag Football Stats Dashboard")

# Load the main stats CSV file
csv_path = "dffl_stats.csv"
if os.path.exists(csv_path):
    print("Loading stats CSV...")
    try:
        df = pd.read_csv(csv_path)
        print("Stats CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading stats CSV: {str(e)}")
        st.stop()
else:
    st.error("Stats CSV file not found. Please ensure 'dffl_stats.csv' is in the repository.")
    st.stop()

# Load the player mapping CSV file
player_mapping_path = "player_mapping.csv"
if os.path.exists(player_mapping_path):
    print("Loading player mapping CSV...")
    try:
        player_mapping = pd.read_csv(player_mapping_path)
        print("Player mapping CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading player mapping CSV: {str(e)}")
        st.stop()
else:
    st.error("Player mapping CSV file not found. Please ensure 'player_mapping.csv' is in the repository.")
    st.stop()

# Load the league mapping CSV file (contains DFFL teams for 2023, 2024, 2025)
league_mapping_path = "league_mapping.csv"
if os.path.exists(league_mapping_path):
    print("Loading league mapping CSV...")
    try:
        league_mapping = pd.read_csv(league_mapping_path)
        print("League mapping CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading league mapping CSV: {str(e)}")
        st.stop()
else:
    st.error("League mapping CSV file not found. Please ensure 'league_mapping.csv' is in the repository.")
    st.stop()

# Convert Spielernummer to integer in both dataframes to ensure matching
df["Spielernummer"] = df["Spielernummer"].astype(int)
player_mapping["Spielernummer"] = player_mapping["Spielernummer"].astype(int)

# Merge the player names into the main dataframe
df = df.merge(
    player_mapping[["Team", "Spielernummer", "Name"]],
    on=["Team", "Spielernummer"],
    how="left"
)

# Create a complete league mapping for all teams and years
# Step 1: Get all unique team-year combinations from the main dataframe
team_year_combinations = df[["Jahr", "Team"]].drop_duplicates()

# Step 2: Initialize the league column based on the year
team_year_combinations["League"] = team_year_combinations["Jahr"].apply(
    lambda x: "Combined" if x <= 2022 else "Other Leagues"
)

# Step 3: Merge with the DFFL teams from league_mapping.csv
# Convert Year in league_mapping to integer to match Jahr
league_mapping["Year"] = league_mapping["Year"].astype(int)
complete_league_mapping = team_year_combinations.merge(
    league_mapping[["Year", "Team", "League"]],
    left_on=["Jahr", "Team"],
    right_on=["Year", "Team"],
    how="left",
    suffixes=("", "_dffl")
)

# Step 4: Update the League column where DFFL data exists
complete_league_mapping["League"] = complete_league_mapping["League_dffl"].combine_first(complete_league_mapping["League"])
complete_league_mapping = complete_league_mapping[["Jahr", "Team", "League"]]

# Step 5: Merge the complete league mapping into the main dataframe
df = df.merge(
    complete_league_mapping,
    on=["Jahr", "Team"],
    how="left"
)

# Initialize session state for selected player and team
if "selected_player" not in st.session_state:
    st.session_state.selected_player = None
if "selected_team" not in st.session_state:
    st.session_state.selected_team = None

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["Top Players", "Player Stats", "Team Stats", "Raw Data"])

with tab1:
    st.header("Top Players")

    # Dropdown for selecting the year (default to 2025)
    years = sorted(df["Jahr"].unique())
    default_year = 2025 if 2025 in years else years[-1]  # Fallback to the latest year if 2025 isn't available
    selected_year = st.selectbox(
        "Select Year",
        years,
        index=years.index(default_year),
        key="top_players_year"
    )

    # Dropdown for selecting the team (default to "All")
    teams = sorted(df["Team"].unique())
    team_options = ["All"] + teams
    selected_team = st.selectbox(
        "Select Team",
        team_options,
        index=0,  # "All" is the first option
        key="top_players_team"
    )

    # Dropdown for selecting the league (default to "DFFL")
    league_options = ["All"] + sorted(df["League"].unique())
    default_league = "DFFL" if "DFFL" in league_options else league_options[0]  # Fallback to the first option if "DFFL" isn't available
    selected_league = st.selectbox(
        "Select League",
        league_options,
        index=league_options.index(default_league),
        key="top_players_league"
    )

    # Dropdown for selecting the event type (default to "Touchdown")
    event_types = sorted(df["Event"].unique())
    default_event = "Touchdown" if "Touchdown" in event_types else event_types[0]  # Fallback to the first event type if "Touchdown" isn't available
    selected_event_type = st.selectbox(
        "Select Event Type",
        event_types,
        index=event_types.index(default_event),
        key="top_players_event_type"
    )

    # Filter data based on selections
    filtered_df = df[(df["Jahr"] == selected_year) & (df["Event"] == selected_event_type)]
    if selected_team != "All":
        filtered_df = filtered_df[filtered_df["Team"] == selected_team]
    if selected_league != "All":
        filtered_df = filtered_df[filtered_df["League"] == selected_league]

    # Group by Team and Spielernummer to ensure all players are included, then merge back the Name
    top_players = filtered_df.groupby(["Team", "Spielernummer"]).agg({"Anzahl": "sum"}).reset_index()
    # Merge the Name column back in after grouping
    top_players = top_players.merge(
        filtered_df[["Team", "Spielernummer", "Name"]].drop_duplicates(),
        on=["Team", "Spielernummer"],
        how="left"
    )
    top_players = top_players.sort_values(by="Anzahl", ascending=False).head(50)

    # Display the top players in a table
    st.subheader(
        f"Top 50 Players for {selected_event_type} in {selected_year}" +
        (f" (Team: {selected_team})" if selected_team != "All" else "") +
        (f" (League: {selected_league})" if selected_league != "All" else "")
    )
    if not top_players.empty:
        # Create a clickable table with Player Number, Player (Name), Team, and Count
        top_players_display = top_players[["Spielernummer", "Name", "Team", "Anzahl"]].rename(
            columns={"Spielernummer": "Player Number", "Name": "Player", "Anzahl": "Count"}
        ).reset_index(drop=True)
        selected_row = st.dataframe(
            top_players_display,
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True
        )

        # If a row is selected, update the session state and switch to the Player Stats tab
        if selected_row["selection"]["rows"]:
            selected_player_index = selected_row["selection"]["rows"][0]
            selected_player = top_players.iloc[selected_player_index]["Spielernummer"]
            selected_team = top_players.iloc[selected_player_index]["Team"]
            st.session_state.selected_player = selected_player
            st.session_state.selected_team = selected_team
            st.session_state.active_tab = "Player Stats"
            st.rerun()
    else:
        st.write("No data available for the selected year, team, league, and event type.")

with tab2:
    st.header("Player Stats")

    # Dropdown for selecting the team
    teams = sorted(df["Team"].unique())
    default_team = st.session_state.selected_team if st.session_state.selected_team in teams else teams[0]
    selected_team = st.selectbox("Select Team", teams, index=teams.index(default_team), key="player_stats_team")

    # Dropdown for selecting the player (filtered by team)
    players = sorted(df[df["Team"] == selected_team]["Spielernummer"].unique())
    default_player = st.session_state.selected_player if st.session_state.selected_player in players else players[0]
    selected_player = st.selectbox("Select Player", players, index=players.index(default_player), key="player_stats_player")

    # Get the player's name (if available)
    player_name = df[(df["Team"] == selected_team) & (df["Spielernummer"] == selected_player)]["Name"].iloc[0] if not df[(df["Team"] == selected_team) & (df["Spielernummer"] == selected_player)]["Name"].isna().all() else "Unknown"

    # Filter data for the selected player and team
    player_data = df[(df["Spielernummer"] == selected_player) & (df["Team"] == selected_team)]

    # Create a pivot table: rows are years, columns are event types, values are counts
    if not player_data.empty:
        pivot_table = player_data.pivot_table(
            values="Anzahl",
            index="Jahr",
            columns="Event",
            aggfunc="sum",
            fill_value=0
        )

        # Convert the index (Jahr) to string to avoid Arrow serialization issues
        pivot_table.index = pivot_table.index.astype(str)

        # Calculate the total row
        total_row = pivot_table.sum().to_frame().T
        total_row.index = ["Total"]

        # Append the Total row to the pivot table
        pivot_table = pd.concat([pivot_table, total_row])

        # Rename columns for display
        pivot_table.index.name = "Year"
        pivot_table.columns.name = "Event Type"

        # Display the pivot table with the Total row styled
        st.subheader(f"Event Counts for {player_name} (Player {selected_player}, Team: {selected_team})")
        st.dataframe(
            pivot_table.style.apply(
                lambda x: ["font-weight: bold; background-color: #f0f0f0"] * len(x) if x.name == "Total" else [""] * len(x),
                axis=1
            )
        )

        # Dropdown for selecting the event type for the visualization
        event_types = sorted(df["Event"].unique())
        selected_event_type = st.selectbox("Select Event Type for Visualization", event_types, key="player_stats_event_type")

        # Filter data for the selected event type
        event_data = player_data[player_data["Event"] == selected_event_type]

        # Plot count over time for the selected event type
        if not event_data.empty:
            fig = px.bar(
                event_data,
                x="Jahr",
                y="Anzahl",
                title=f"Count of {selected_event_type} for {player_name} (Player {selected_player}, Team: {selected_team}) Over Time",
                labels={"Jahr": "Year", "Anzahl": "Count"},
            )
            fig.update_xaxes(tickvals=event_data["Jahr"].astype(int))
            st.plotly_chart(fig)
        else:
            st.write(f"No data available for {selected_event_type} for this player.")
    else:
        st.write("No data available for this player and team combination.")

with tab3:
    st.header("Team Stats")

    # Dropdown for selecting the team
    teams = sorted(df["Team"].unique())
    selected_team = st.selectbox("Select Team", teams, key="team_stats_team")

    # Filter data for the selected team
    team_data = df[df["Team"] == selected_team]

    # Create a pivot table: rows are years, columns are event types, values are counts
    if not team_data.empty:
        pivot_table = team_data.pivot_table(
            values="Anzahl",
            index="Jahr",
            columns="Event",
            aggfunc="sum",
            fill_value=0
        )

        # Convert the index (Jahr) to string to avoid Arrow serialization issues
        pivot_table.index = pivot_table.index.astype(str)

        # Calculate the total row
        total_row = pivot_table.sum().to_frame().T
        total_row.index = ["Total"]

        # Append the Total row to the pivot table
        pivot_table = pd.concat([pivot_table, total_row])

        # Rename columns for display
        pivot_table.index.name = "Year"
        pivot_table.columns.name = "Event Type"

        # Display the pivot table with the Total row styled
        st.subheader(f"Event Counts for Team {selected_team}")
        st.dataframe(
            pivot_table.style.apply(
                lambda x: ["font-weight: bold; background-color: #f0f0f0"] * len(x) if x.name == "Total" else [""] * len(x),
                axis=1
            )
        )

        # Dropdown for selecting the event type for the visualization
        event_types = sorted(df["Event"].unique())
        selected_event_type = st.selectbox("Select Event Type for Visualization", event_types, key="team_stats_event_type")

        # Filter data for the selected event type
        event_data = team_data[team_data["Event"] == selected_event_type]

        # Plot count over time for the selected event type
        if not event_data.empty:
            fig = px.bar(
                event_data,
                x="Jahr",
                y="Anzahl",
                title=f"Count of {selected_event_type} for Team {selected_team} Over Time",
                labels={"Jahr": "Year", "Anzahl": "Count"},
            )
            fig.update_xaxes(tickvals=event_data["Jahr"].astype(int))
            st.plotly_chart(fig)
        else:
            st.write(f"No data available for {selected_event_type} for this team.")
    else:
        st.write("No data available for this team.")

with tab4:
    st.header("Raw Data")

    # Dropdowns for filtering raw data
    teams = sorted(df["Team"].unique())
    selected_team = st.selectbox("Select Team", ["All"] + teams, key="raw_data_team")
    years = sorted(df["Jahr"].unique())
    selected_year = st.selectbox("Select Year", ["All"] + years, key="raw_data_year")

    # Filter the raw data
    raw_data = df.copy()
    if selected_team != "All":
        raw_data = raw_data[raw_data["Team"] == selected_team]
    if selected_year != "All":
        raw_data = raw_data[raw_data["Jahr"] == selected_year]

    # Display the raw data with renamed columns
    raw_data_display = raw_data.rename(
        columns={
            "Spielernummer": "Player Number",
            "Name": "Player",
            "Anzahl": "Count",
            "Jahr": "Year",
            "Event": "Event Type",
            "Team": "Team",
            "League": "League"
        }
    )
    st.write(raw_data_display)