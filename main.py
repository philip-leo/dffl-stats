import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from PIL import Image
import io

# Function to clean player number
def clean_player_number(value):
    if pd.isna(value):
        return None
    try:
        # Convert to string first to handle any numeric formats
        str_value = str(value).strip()
        # Remove any non-numeric characters
        cleaned = ''.join(filter(str.isdigit, str_value))
        # Convert to integer and ensure it's within reasonable range (1-99)
        cleaned_int = int(cleaned) if cleaned else None
        if cleaned_int and 0 < cleaned_int < 100:  # Only accept numbers between 1 and 99
            return cleaned_int
        return None
    except Exception as e:
        print(f"Error cleaning player number value '{value}': {str(e)}")
        return None

# Set wide page layout and other configurations
st.set_page_config(
    page_title="Flag Football Stats Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="auto"
)

# Add custom CSS for a more balanced width
st.markdown("""
    <style>
        .main > div {
            max-width: 70%;
            margin: auto;
        }
        /* Remove the previous dataframe CSS that was causing issues */
    </style>
""", unsafe_allow_html=True)

def get_base64_image(image_path, size=(30, 30)):
    try:
        if pd.isna(image_path) or not os.path.exists(image_path):
            return None
        img = Image.open(image_path)
        img = img.resize(size)  # Resize image to desired dimensions
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

st.title("Flag Football Stats Dashboard")

# Load the main stats CSV
csv_path = "dffl_stats.csv"
if os.path.exists(csv_path):
    print("Loading stats CSV...")
    try:
        # Load the CSV with explicit dtypes using English column names
        df = pd.read_csv(csv_path, dtype={
            'Team': str,
            'Player Number': str,
            'Count': int,
            'Event': str,
            'Year': int
        })
        
        print("First few rows of stats CSV:")
        print(df.head())
        print("\nColumns in stats CSV:", df.columns.tolist())
        print("Dtypes of stats CSV:")
        print(df.dtypes)
        
        # Clean Player Number in main dataframe
        print("\nCleaning Player Number...")
        df["Player Number"] = df["Player Number"].apply(clean_player_number)
        df["Player Number"] = df["Player Number"].astype("Int64")
        
        # Print sample after cleaning
        print("Sample of cleaned Player Numbers:")
        print(df[["Team", "Player Number"]].head())
        
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
        # Load the CSV with explicit dtypes
        player_mapping = pd.read_csv(player_mapping_path, dtype={
            'Team': str,
            'Player Number': str,
            'First Name': str,
            'Last Name': str
        })
        
        print("First few rows of player mapping CSV:")
        print(player_mapping.head())
        print("Columns in player mapping CSV:", player_mapping.columns.tolist())
        
        # Clean Player Number
        print("\nCleaning Player Number...")
        player_mapping["Player Number"] = player_mapping["Player Number"].apply(clean_player_number)
        player_mapping["Player Number"] = player_mapping["Player Number"].astype("Int64")
        
        # Create the Name column by concatenating First Name and Last Name
        print("\nCreating Name column...")
        player_mapping["Name"] = player_mapping.apply(
            lambda x: f"{str(x['First Name']).strip() if pd.notna(x['First Name']) else ''} {str(x['Last Name']).strip() if pd.notna(x['Last Name']) else ''}".strip(),
            axis=1
        )
        
        # Print sample after processing
        print("Sample after processing:")
        print(player_mapping[["Team", "Player Number", "Name"]].head())
        
        # Create subset with only needed columns AFTER creating the Name column
        print("\nCreating player mapping subset...")
        player_mapping_subset = player_mapping[["Team", "Player Number", "Name"]].copy()
        print("Columns in player_mapping_subset:", player_mapping_subset.columns.tolist())
        
        print("\nFinal validation:")
        print("Debug: Columns in df:", df.columns.tolist())
        print("Debug: Columns in player_mapping:", player_mapping.columns.tolist())
        print("Debug: Sample of df Team and Player Number:")
        print(df[["Team", "Player Number"]].head())
        print("Debug: Sample of player_mapping Team and Player Number:")
        print(player_mapping[["Team", "Player Number", "Name"]].head())
        
    except Exception as e:
        print(f"Error processing player mapping: {str(e)}")
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

# Load the team info CSV file
team_info_path = "team_info.csv"
if os.path.exists(team_info_path):
    print("Loading team info CSV...")
    try:
        team_info = pd.read_csv(team_info_path)
        print("Team info CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading team info CSV: {str(e)}")
        st.stop()
else:
    st.error("Team info CSV file not found. Please ensure 'team_info.csv' is in the repository.")
    st.stop()

# Clean and validate Player Number in both dataframes
print("\nCleaning and validating Player Number...")

# Ensure Team column is string type in both dataframes
df["Team"] = df["Team"].astype(str)
player_mapping["Team"] = player_mapping["Team"].astype(str)

# Print debug information
print("\nFinal validation:")
print("Debug: Columns in df:", df.columns.tolist())
print("Debug: Columns in player_mapping:", player_mapping.columns.tolist())
print("Debug: Sample of df Team and Player Number:")
print(df[["Team", "Player Number"]].head())
print("Debug: Sample of player_mapping Team and Player Number:")
print(player_mapping[["Team", "Player Number", "Name"]].head())

# Print debug information before merge
print("\nPre-merge validation:")
print("Available columns in player_mapping:", player_mapping.columns.tolist())
print("Sample of player_mapping data:")
print(player_mapping.head())

# Merge the player names into the main dataframe
try:
    df = df.merge(
        player_mapping_subset,
        on=["Team", "Player Number"],
        how="left",
        validate="m:1"  # many-to-one relationship
    )
    
    print("\nPost-merge validation:")
    print("Columns in merged dataframe:", df.columns.tolist())
    
except Exception as e:
    print(f"Debug: Error during merge: {str(e)}")
    print("Debug: DataFrame info:")
    print(df.info())
    print("\nDebug: Player mapping info:")
    print(player_mapping.info())
    st.error(f"Error merging player data: {str(e)}")
    st.stop()

# Create a complete league mapping for all teams and years
# Step 1: Get all unique team-year combinations from the main dataframe
team_year_combinations = df[["Year", "Team"]].drop_duplicates()

# Step 2: Initialize the league column based on the year
team_year_combinations["League"] = team_year_combinations["Year"].apply(
    lambda x: "Combined" if x <= 2022 else "Other Leagues"
)

# Step 3: Merge with the DFFL teams from league_mapping.csv
# Convert Year in league_mapping to integer to match Year
league_mapping["Year"] = league_mapping["Year"].astype(int)
complete_league_mapping = team_year_combinations.merge(
    league_mapping[["Year", "Team", "League"]],
    left_on=["Year", "Team"],
    right_on=["Year", "Team"],
    how="left",
    suffixes=("", "_dffl")
)

# Step 4: Update the League column where DFFL data exists
complete_league_mapping["League"] = complete_league_mapping["League_dffl"].combine_first(complete_league_mapping["League"])
complete_league_mapping = complete_league_mapping[["Year", "Team", "League"]]

# Step 5: Merge the complete league mapping into the main dataframe
df = df.merge(
    complete_league_mapping,
    on=["Year", "Team"],
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
    # Dropdown for selecting the year (default to 2025)
    years = sorted(df["Year"].unique())
    default_year = 2025 if 2025 in years else years[-1]
    selected_year = st.selectbox(
        "Select Year",
        years,
        index=years.index(default_year),
        key="top_players_year"
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
    filtered_df = df[(df["Year"] == selected_year) & (df["Event"] == selected_event_type)]
    if selected_league != "All":
        filtered_df = filtered_df[filtered_df["League"] == selected_league]

    # Group by Team and Player Number to ensure all players are included, then merge back the Name
    top_players = filtered_df.groupby(["Team", "Player Number"]).agg({"Count": "sum"}).reset_index()
    top_players = top_players.merge(
        filtered_df[["Team", "Player Number", "Name"]].drop_duplicates(),
        on=["Team", "Player Number"],
        how="left"
    )
    top_players = top_players.sort_values(by="Count", ascending=False).head(50)

    # Display the top players in a table
    st.subheader(
        f"Top 50 Players for {selected_event_type} in {selected_year}" +
        (f" (League: {selected_league})" if selected_league != "All" else "")
    )
    if not top_players.empty:
        # Create a clickable table with Player Number, Player (Name), Team Logo, Team Name, and Count
        top_players_display = top_players[["Player Number", "Name", "Team", "Count"]].rename(
            columns={"Player Number": "#", "Name": "Player", "Team": "Team Name"}
        ).reset_index(drop=True)

        # Get team logos from team_info and convert to base64
        workspace_dir = os.path.dirname(os.path.abspath(__file__))
        team_logos = {
            team: get_base64_image(os.path.join(workspace_dir, logo_path)) if pd.notna(logo_path) else None
            for team, logo_path in zip(team_info['Team'], team_info['LogoPath'])
        }
        
        # Add team logo column with base64 encoded images
        top_players_display.insert(2, "Team Logo", top_players_display["Team Name"].map(team_logos))

        # Display the table with custom column configurations
        st.dataframe(
            top_players_display,
            hide_index=True,
            use_container_width=True,
            height=len(top_players_display) * 35 + 40,
            column_config={
                "#": st.column_config.NumberColumn(
                    help="Player number",
                    width="small"
                ),
                "Player": st.column_config.TextColumn(
                    width="medium"
                ),
                "Team Logo": st.column_config.ImageColumn(
                    "Logo",
                    help="Team logo",
                    width="small"
                ),
                "Team Name": st.column_config.TextColumn(
                    "Team",
                    width="medium"
                ),
                "Count": st.column_config.NumberColumn(
                    width="small"
                )
            }
        )
    else:
        st.write("No data available for the selected year, team, league, and event type.")

with tab2:
    # Dropdown for selecting the team
    teams = sorted(df["Team"].unique())
    default_team = teams[0]
    selected_team = st.selectbox("Select Team", teams, index=teams.index(default_team), key="player_stats_team")

    # Get players for the selected team, handling NA values
    team_players = df[df["Team"] == selected_team].copy()
    # Remove rows where Player Number is NA
    team_players = team_players[team_players["Player Number"].notna()]
    players = sorted(team_players["Player Number"].unique())
    
    if len(players) > 0:
        default_player = players[0]
        selected_player = st.selectbox("Select Player", players, index=players.index(default_player), key="player_stats_player")

        # Get the player's name (if available)
        player_data = df[
            (df["Team"] == selected_team) & 
            (df["Player Number"] == selected_player)
        ]
        player_name = player_data["Name"].iloc[0] if not player_data["Name"].isna().all() else "Unknown"

        # Create a pivot table for career statistics
        if not player_data.empty:
            pivot_table = player_data.pivot_table(
                values="Count",
                index="Year",
                columns="Event",
                aggfunc="sum",
                fill_value=0
            )

            # Convert the index (Year) to string to avoid Arrow serialization issues
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
            st.subheader(f"Career Stats for {player_name}")
            st.dataframe(
                pivot_table.style.apply(
                    lambda x: ["font-weight: bold; background-color: #f0f0f0"] * len(x) if x.name == "Total" else [""] * len(x),
                    axis=1
                ),
                use_container_width=True,
                height=len(pivot_table) * 35 + 40
            )

        # Dropdown for selecting the event type
        event_types = sorted(df["Event"].unique())
        selected_event_type = st.selectbox("Select Event Type", event_types, key="player_stats_event_type")

        # Filter data for the selected event type
        event_data = player_data[player_data["Event"] == selected_event_type].groupby("Year")["Count"].sum().reset_index()

        # Plot count over time for the selected event type
        if not event_data.empty:
            fig = px.bar(
                event_data,
                x="Year",
                y="Count",
                title=f"Count of {selected_event_type} for {player_name} Over Time",
                labels={"Year": "Year", "Count": "Count"},
            )
            fig.update_xaxes(tickvals=event_data["Year"].astype(int))
            st.plotly_chart(fig)
        else:
            st.write(f"No data available for {selected_event_type} for this player.")
    else:
        st.write(f"No players found for team {selected_team}")

with tab3:
    # Dropdown for selecting the team
    teams = sorted(df["Team"].unique())
    selected_team = st.selectbox("Select Team", teams, key="team_stats_team")

    # Display team information if available
    team_info_row = team_info[team_info["Team"] == selected_team]
    if not team_info_row.empty:
        # Create two columns for team info
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display team logo if it exists
            logo_path = team_info_row["LogoPath"].iloc[0]
            try:
                if os.path.exists(logo_path):
                    st.image(logo_path, width=200)
                else:
                    st.info("🖼️ Team logo coming soon")
            except Exception as e:
                st.info("🖼️ Team logo coming soon")
        
        with col2:
            st.subheader(selected_team)
            
            # Display description with proper line breaks
            description = team_info_row["Description"].iloc[0]
            if pd.notna(description):
                for line in description.split("\n"):
                    st.write(line)
            
            # Display Instagram link if available
            instagram_url = team_info_row["InstagramURL"].iloc[0]
            if pd.notna(instagram_url) and instagram_url:
                st.markdown(f"[Instagram]({instagram_url})")

    # Add a separator
    st.markdown("---")

    # Filter data for the selected team
    team_data = df[df["Team"] == selected_team]

    # Create a pivot table: rows are years, columns are event types, values are counts
    if not team_data.empty:
        pivot_table = team_data.pivot_table(
            values="Count",
            index="Year",
            columns="Event",
            aggfunc="sum",
            fill_value=0
        )

        # Convert the index (Year) to string to avoid Arrow serialization issues
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
            ),
            use_container_width=True,
            height=len(pivot_table) * 35 + 40
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
                x="Year",
                y="Count",
                title=f"Count of {selected_event_type} for Team {selected_team} Over Time",
                labels={"Year": "Year", "Count": "Count"},
            )
            fig.update_xaxes(tickvals=event_data["Year"].astype(int))
            st.plotly_chart(fig)
        else:
            st.write(f"No data available for {selected_event_type} for this team.")

        # New section: Detailed player stats for the selected year
        st.subheader(f"Player Statistics")
        
        # Dropdown for selecting the year (moved here)
        years = sorted(df["Year"].unique())
        default_year = 2025 if 2025 in years else years[-1]  # Fallback to the latest year if 2025 isn't available
        selected_year = st.selectbox(
            "Select Year",
            years,
            index=years.index(default_year),
            key="team_stats_year"
        )

        # Filter data for the selected team and year
        team_year_data = df[(df["Team"] == selected_team) & (df["Year"] == selected_year)]
        
        if not team_year_data.empty:
            # Remove rows with NA player numbers
            team_year_data = team_year_data[team_year_data["Player Number"].notna()]
            
            # Get unique players for this team and year, ensuring we have the correct player information
            players = team_year_data[["Player Number", "Name"]].drop_duplicates()
            
            # Print debug information
            print(f"\nDebug: Players for {selected_team} in {selected_year}:")
            print(players)
            
            if not players.empty:
                # Create player stats DataFrame
                player_stats = []
                for _, player in players.iterrows():
                    player_data = team_year_data[team_year_data["Player Number"] == player["Player Number"]]
                    
                    # Create stats dictionary with player info
                    stats = {
                        "#": player["Player Number"],
                        "Player": player["Name"] if pd.notna(player["Name"]) else "None"
                    }
                    
                    # Add stats for each event type
                    event_types = sorted([
                        event for event in df["Event"].unique()
                        if event not in ["Overtime", "Safety (+1)"]
                    ])
                    
                    for event in event_types:
                        event_count = player_data[player_data["Event"] == event]["Count"].sum()
                        stats[event] = event_count
                    
                    player_stats.append(stats)

                # Convert to DataFrame and sort
                player_stats_df = pd.DataFrame(player_stats)
                
                # Sort by Touchdown in descending order if it exists, otherwise by the first event type
                if "Touchdown" in player_stats_df.columns:
                    player_stats_df = player_stats_df.sort_values("Touchdown", ascending=False)
                elif len(event_types) > 0:
                    player_stats_df = player_stats_df.sort_values(event_types[0], ascending=False)

                # Display the player stats table
                st.dataframe(
                    player_stats_df,
                    hide_index=True,
                    use_container_width=True,
                    height=len(player_stats_df) * 35 + 40,
                    column_config={
                        "#": st.column_config.NumberColumn(
                            help="Player number",
                            width="small"
                        ),
                        "Player": st.column_config.TextColumn(
                            width="medium"
                        ),
                        **{
                            event: st.column_config.NumberColumn(
                                width="small"
                            )
                            for event in player_stats_df.columns
                            if event not in ["#", "Player"]
                        }
                    }
                )
            else:
                st.write(f"No players found for team {selected_team} in {selected_year}")
        else:
            st.write(f"No data available for team {selected_team} in {selected_year}")
    else:
        st.write("No data available for this team.")

with tab4:
    # Dropdowns for filtering raw data
    teams = sorted(df["Team"].unique())
    selected_team = st.selectbox("Select Team", ["All"] + teams, key="raw_data_team")
    years = sorted(df["Year"].unique())
    selected_year = st.selectbox("Select Year", ["All"] + years, key="raw_data_year")

    # Filter the raw data
    raw_data = df.copy()
    if selected_team != "All":
        raw_data = raw_data[raw_data["Team"] == selected_team]
    if selected_year != "All":
        raw_data = raw_data[raw_data["Year"] == selected_year]

    # Display the raw data with renamed columns
    raw_data_display = raw_data.rename(
        columns={
            "Player Number": "#",
            "Name": "Player",
            "Count": "Count",
            "Year": "Year",
            "Event": "Event Type",
            "Team": "Team",
            "League": "League"
        }
    )
    st.dataframe(
        raw_data_display,
        use_container_width=True,
        height=400,
        column_config={
            "#": st.column_config.NumberColumn(
                help="Player number",
                width="small"
            ),
            "Player": st.column_config.TextColumn(
                width="medium"
            ),
            "Count": st.column_config.NumberColumn(
                width="small"
            ),
            "Year": st.column_config.NumberColumn(
                width="small"
            ),
            "Event Type": st.column_config.TextColumn(
                width="medium"
            ),
            "Team": st.column_config.TextColumn(
                width="medium"
            ),
            "League": st.column_config.TextColumn(
                width="medium"
            )
        }
    )