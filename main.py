# Flag Football Stats Dashboard
# Updated 2025-04-30: Fixed data loading and year filtering issues

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from PIL import Image
import io
from config import standardize_dataframe, EXPECTED_COLUMNS

# Function to clean player number
def clean_player_number(value):
    if pd.isna(value):
        return None
    try:
        # Convert to float first to handle decimal format
        float_value = float(str(value).strip())
        # Convert to integer
        return int(float_value)
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

def get_base64_image(image_path):
    """Convert an image to base64 string."""
    try:
        if pd.isna(image_path) or not os.path.exists(image_path):
            return None
        with Image.open(image_path) as img:
            # Resize image to a reasonable size for the table
            img.thumbnail((30, 30))
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error loading image {image_path}: {str(e)}")
        return None

st.title("Flag Football Stats Dashboard")

# Load the main stats CSV
historic_path = "dffl_stats_historic.csv"
current_path = "dffl_stats_2025.csv"

# Updated 2025-04-30: Fixed data loading and year filtering
try:
    print("Loading historic data...")
    historic_df = pd.read_csv(historic_path)  # Remove dtype mapping
    print(f"Historic data loaded successfully. Shape: {historic_df.shape}")
    historic_df = standardize_dataframe(historic_df, is_german=True)
    print("Historic data standardized successfully")
    
    print("Loading 2025 data...")
    current_df = pd.read_csv(current_path)  # Remove dtype mapping
    print(f"2025 data loaded successfully. Shape: {current_df.shape}")
    print("Sample of 2025 data:")
    print(current_df.head())
    current_df = standardize_dataframe(current_df, is_german=False)  # Already in English
    print("2025 data standardized successfully")
    
    # Combine the dataframes
    df = pd.concat([historic_df, current_df], ignore_index=True)
    
    # Ensure Year is integer type
    df["Year"] = df["Year"].astype(int)
    
    print(f"Combined data shape: {df.shape}")
    print("Sample of combined data:")
    print(df[df['Year'] == 2025].head())
    
    # Clean Player Number in combined dataframe
    print("\nCleaning Player Number...")
    df["Player Number"] = df["Player Number"].apply(clean_player_number)
    df["Player Number"] = df["Player Number"].astype("Int64")
    
    # Print sample after cleaning
    print("Sample of cleaned Player Numbers:")
    print(df[["Team", "Player Number", "Year"]].head())
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    print(f"Detailed error: {str(e)}")
    print(f"Error type: {type(e)}")
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

# Get URL parameters using the new API
params = st.query_params
if "player" in params and "team" in params:
    st.session_state.selected_player = int(params["player"])
    st.session_state.selected_team = params["team"]

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
    print(f"\nDebug: Filtering data for year {selected_year} and event {selected_event_type}")
    print(f"Debug: Available years in df: {df['Year'].unique()}")
    print(f"Debug: Available events in df: {df['Event'].unique()}")
    print(f"Debug: Shape of df before filtering: {df.shape}")
    
    filtered_df = df[(df["Year"] == selected_year) & (df["Event"] == selected_event_type)]
    print(f"Debug: Shape after year and event filter: {filtered_df.shape}")
    print(f"Debug: Sample of filtered data:")
    print(filtered_df.head())
    
    if selected_league != "All":
        filtered_df = filtered_df[filtered_df["League"] == selected_league]
        print(f"Debug: Shape after league filter: {filtered_df.shape}")
        print(f"Debug: Available leagues in filtered data: {filtered_df['League'].unique()}")

    # Group by Team and Player Number to ensure all players are included, then merge back the Name
    top_players = filtered_df.groupby(["Team", "Player Number"]).agg({"Count": "sum"}).reset_index()
    print(f"Debug: Shape after grouping: {top_players.shape}")
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
        # Merge with player_mapping to get profile pictures
        top_players = top_players.merge(
            player_mapping[["Team", "Player Number", "ProfilePicture"]],
            on=["Team", "Player Number"],
            how="left"
        )
        
        # Create a clickable table with Player Number, Profile Picture, Player (Name), Team Logo, Team Name, and Count
        top_players_display = top_players[["Player Number", "ProfilePicture", "Name", "Count"]].rename(
            columns={
                "Player Number": "#",
                "ProfilePicture": "Profile",
                "Name": "Player"
            }
        ).reset_index(drop=True)

        # Get team logos from team_info and convert to base64
        team_logos = {
            team: get_base64_image(logo_path) if pd.notna(logo_path) else None
            for team, logo_path in zip(team_info['Team'], team_info['LogoPath'])
        }
        
        # Add team logo column with base64 encoded images
        top_players_display.insert(1, "Team", top_players["Team"].map(team_logos))

        # Display the table with custom column configurations
        st.dataframe(
            top_players_display,
            hide_index=True,
            use_container_width=True,
            height=len(top_players_display) * 35 + 40,
            column_config={
                "#": st.column_config.NumberColumn(
                    help="Player number",
                    width=35  # Even slimmer width for player number
                ),
                "Team": st.column_config.ImageColumn(
                    help="Team logo",
                    width=45  # Slimmer width for team logo
                ),
                "Profile": st.column_config.ImageColumn(
                    help="Player photo",
                    width=45  # Slimmer width for profile picture
                ),
                "Player": st.column_config.TextColumn(
                    width="small",  # Changed from medium to small
                    help="Click on player name to view detailed stats"
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
    default_team_index = teams.index(st.session_state.selected_team) if st.session_state.selected_team in teams else 0
    selected_team = st.selectbox("Select Team", teams, index=default_team_index, key="player_stats_team")

    # Get players for the selected team, handling NA values
    team_players = df[df["Team"] == selected_team].copy()
    # Remove rows where Player Number is NA
    team_players = team_players[team_players["Player Number"].notna()]
    players = sorted(team_players["Player Number"].unique())
    
    if len(players) > 0:
        # Set default player based on session state or first player
        default_player_index = players.index(st.session_state.selected_player) if st.session_state.selected_player in players else 0
        selected_player = st.selectbox("Select Player", players, index=default_player_index, key="player_stats_player")

        # Get player details from the mapping
        player_info = player_mapping[
            (player_mapping['Team'] == selected_team) & 
            (player_mapping['Player Number'] == selected_player)
        ]
        
        if not player_info.empty:
            player_info = player_info.iloc[0]
            player_name = f"{player_info['First Name']} {player_info['Last Name']}"
            
            # Display player image if available
            if pd.notna(player_info.get('ProfilePicture')) and str(player_info['ProfilePicture']).strip():
                try:
                    st.image(player_info['ProfilePicture'], width=200)
                except Exception as e:
                    print(f"Error loading player image: {str(e)}")
                    st.info("Unable to load player image")
        else:
            player_name = "Unknown Player"
        
        # Create a pivot table for career statistics
        if not team_players.empty:
            # Filter for the current player first
            player_stats = team_players[team_players["Player Number"] == selected_player]
            
            pivot_table = player_stats.pivot_table(
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
                    lambda x: ['background-color: rgba(128, 128, 128, 0.2); font-weight: bold'] * len(x) if x.name == "Total" else [""] * len(x),
                    axis=1
                ),
                use_container_width=True,
                height=len(pivot_table) * 35 + 40
            )

        # Dropdown for selecting the event type
        event_types = sorted(df["Event"].unique())
        selected_event_type = st.selectbox("Select Event Type", event_types, key="player_stats_event_type")

        # Filter data for the selected event type and sum by year
        event_data = team_players[
            (team_players["Event"] == selected_event_type) & 
            (team_players["Player Number"] == selected_player)
        ].groupby("Year")["Count"].sum().reset_index()
        
        # Plot count over time for the selected event type
        if not event_data.empty:
            fig = px.bar(
                event_data,
                x="Year",
                y="Count",
                title=f"{selected_event_type} per Year for {player_name}",
                labels={"Count": "Number of Events", "Year": "Year"},
                color_discrete_sequence=["#1f77b4"]
            )
            fig.update_xaxes(tickvals=event_data["Year"].astype(int))
            fig.update_layout(
                dragmode=False,  # Disable pan
                showlegend=False,
                xaxis=dict(fixedrange=True),  # Disable zoom on x-axis
                yaxis=dict(fixedrange=True)   # Disable zoom on y-axis
            )
            # Add data labels on top of bars with increased size and padding
            fig.update_traces(
                text=event_data["Count"],
                textposition='outside',
                textfont=dict(size=16),
                texttemplate='%{text:d}',  # Format as integer
                cliponaxis=False           # Ensure labels are visible even if they extend beyond the plot
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"player_chart_{selected_player}_{selected_event_type}")
        else:
            st.write(f"No data available for {selected_event_type} for this player.")

        # New section: Per-game stats for selected year
        st.subheader("Per-Game Stats")
        
        # Dropdown for selecting the year
        years = sorted(df["Year"].unique())
        default_year = 2025 if 2025 in years else years[-1]
        selected_year = st.selectbox(
            "Select Year for Per-Game Stats",
            years,
            index=years.index(default_year),
            key="player_per_game_year"
        )

        # Load detailed stats for the selected year
        detail_file = "dffl_stats_detail_2025.csv" if selected_year == 2025 else "dffl_stats_detail_historic.csv"
        try:
            # Load the detailed stats
            detail_df = pd.read_csv(detail_file)
            
            # Add Count column (each row represents one event)
            detail_df['Count'] = 1
            
            # Convert date to datetime and extract year
            detail_df['Year'] = pd.to_datetime(detail_df['Datum'], format='%d.%m.%Y').dt.year
            
            # Standardize the dataframe
            detail_df = standardize_dataframe(detail_df, is_german=True)
            
            # Filter for the selected player, team, and year
            player_detail_df = detail_df[
                (detail_df["Team"] == selected_team) & 
                (detail_df["Player Number"] == selected_player) &
                (detail_df["Year"] == selected_year)  # Add year filter here
            ]
            
            # Merge with player mapping to get player name (if available)
            player_detail_df = player_detail_df.merge(
                player_mapping[["Team", "Player Number", "Name"]],
                on=["Team", "Player Number"],
                how="left"
            )
            
            if not player_detail_df.empty:
                # Group by game (using Date and Scheduled Time) and create a pivot table
                game_stats = player_detail_df.pivot_table(
                    values="Count",
                    index=["Date", "Matchday", "Opponent", "Scheduled Time"],
                    columns="Event",
                    aggfunc="sum",
                    fill_value=0
                ).reset_index()
                
                # Convert date to datetime for proper sorting
                game_stats['Date'] = pd.to_datetime(game_stats['Date'], format='%d.%m.%Y')
                
                # Sort by Date first, then by Scheduled Time
                game_stats = game_stats.sort_values(['Date', 'Scheduled Time'])
                
                # Convert date back to string format for display
                game_stats['Date'] = game_stats['Date'].dt.strftime('%d.%m.%Y')
                
                # Get opponent logos from team_info
                opponent_logos = {
                    team: get_base64_image(logo_path) if pd.notna(logo_path) else None
                    for team, logo_path in zip(team_info['Team'], team_info['LogoPath'])
                }
                
                # Add opponent logo column
                game_stats['Logo'] = game_stats['Opponent'].map(opponent_logos)
                
                # Rename columns for display
                game_stats = game_stats.rename(columns={
                    "Date": "Date",
                    "Opponent": "Opponent"
                })
                
                # Reorder columns to put date/matchday info first, excluding Time
                info_columns = ["Date", "Matchday", "Logo", "Opponent"]
                event_columns = [col for col in game_stats.columns if col not in info_columns + ["Scheduled Time"]]
                game_stats = game_stats[info_columns + event_columns]
                
                # Calculate totals for each event type
                totals = game_stats[event_columns].sum()
                
                # Create a summary row (with empty string for Logo instead of None)
                summary_row = pd.DataFrame({
                    "Date": ["Season Total"],
                    "Matchday": [""],
                    "Logo": [""],  # Empty string instead of None
                    "Opponent": [""],
                    **{col: [totals[col]] for col in event_columns}
                })
                
                # Append the summary row to the game stats
                game_stats = pd.concat([game_stats, summary_row], ignore_index=True)
                
                # Display the table with styled summary row
                st.dataframe(
                    game_stats.style.apply(
                        lambda x: ['background-color: rgba(128, 128, 128, 0.2); font-weight: bold'] * len(x) if x.name == len(game_stats) - 1 else [""] * len(x),
                        axis=1
                    ),
                    hide_index=True,
                    use_container_width=True,
                    height=len(game_stats) * 35 + 40,
                    column_config={
                        "Logo": st.column_config.ImageColumn(
                            "Team Logo",
                            help="Opponent's team logo",
                            width="small"
                        ),
                        "Matchday": st.column_config.TextColumn(
                            "Matchday",
                            width="small"
                        )
                    }
                )
            else:
                st.write(f"No per-game stats available for {player_name} in {selected_year}")
        except Exception as e:
            st.error(f"Error loading per-game stats: {str(e)}")
            print(f"Detailed error: {str(e)}")
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
                lambda x: ['background-color: rgba(128, 128, 128, 0.2); font-weight: bold'] * len(x) if x.name == "Total" else [""] * len(x),
                axis=1
            ),
            use_container_width=True,
            height=len(pivot_table) * 35 + 40
        )

        # Dropdown for selecting the event type for the visualization
        event_types = sorted(df["Event"].unique())
        selected_event_type = st.selectbox("Select Event Type for Visualization", event_types, key="team_stats_event_type")

        # Filter data for the selected event type and sum by year
        event_data = team_data[team_data["Event"] == selected_event_type].groupby("Year")["Count"].sum().reset_index()
        
        # Plot count over time for the selected event type
        if not event_data.empty:
            fig = px.bar(
                event_data,
                x="Year",
                y="Count",
                title=f"{selected_event_type} per Year",
                labels={"Count": "Number of Events", "Year": "Year"},
                color_discrete_sequence=["#1f77b4"]
            )
            fig.update_xaxes(tickvals=event_data["Year"].astype(int))
            fig.update_layout(
                dragmode=False,  # Disable pan
                showlegend=False,
                xaxis=dict(fixedrange=True),  # Disable zoom on x-axis
                yaxis=dict(fixedrange=True)   # Disable zoom on y-axis
            )
            # Add data labels on top of bars with increased size and padding
            fig.update_traces(
                text=event_data["Count"],
                textposition='outside',
                textfont=dict(size=16),
                texttemplate='%{text:d}',  # Format as integer
                cliponaxis=False           # Ensure labels are visible even if they extend beyond the plot
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"team_chart_{selected_team}_{selected_event_type}")
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
                    
                    # Get player's profile picture from player_mapping
                    player_profile = player_mapping[
                        (player_mapping["Team"] == selected_team) & 
                        (player_mapping["Player Number"] == player["Player Number"])
                    ]["ProfilePicture"].iloc[0] if not player_mapping[
                        (player_mapping["Team"] == selected_team) & 
                        (player_mapping["Player Number"] == player["Player Number"])
                    ].empty else None
                    
                    # Create stats dictionary with player info
                    stats = {
                        "#": player["Player Number"],
                        "Profile": player_profile,
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
                            width=50
                        ),
                        "Profile": st.column_config.ImageColumn(
                            help="Player photo",
                            width=60
                        ),
                        "Player": st.column_config.TextColumn(
                            width="medium"
                        ),
                        **{
                            event: st.column_config.NumberColumn(
                                width="small"
                            )
                            for event in player_stats_df.columns
                            if event not in ["#", "Profile", "Player"]
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
        height=50 * 35 + 40,  # 50 rows * 35px per row + 40px for header
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