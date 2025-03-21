import streamlit as st
import pandas as pd
import os
from fetch_csv import fetch_dffl_csv
import plotly.express as px  # For interactive visualizations

st.title("Flag Football Stats Dashboard")

# Check if the CSV file exists
csv_path = "dffl_stats.csv"

# Add a button to refresh the data if needed
if st.button("Refresh Data"):
    st.write("Fetching data...")
    try:
        csv_path = fetch_dffl_csv()
        st.write("Fetching completed!")
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.stop()

# Load the CSV file
if os.path.exists(csv_path):
    st.write("Loading CSV...")
    try:
        df = pd.read_csv(csv_path)
        st.write("CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        st.stop()
else:
    st.write("CSV file not found. Fetching data...")
    try:
        csv_path = fetch_dffl_csv()
        st.write("Fetching completed!")
        df = pd.read_csv(csv_path)
        st.write("CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.stop()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["Raw Data", "Player Stats", "Team Stats"])

# Tab 1: Raw Data with Filtering
with tab1:
    st.subheader("Raw Data")
    
    # Add filters
    st.write("Filter the data:")
    teams = sorted(df["Team"].unique())
    selected_team = st.multiselect("Select Team(s)", teams, default=teams)
    
    years = sorted(df["Jahr"].unique())
    selected_year = st.multiselect("Select Year(s)", years, default=years)
    
    player_numbers = sorted(df["Spielernummer"].unique())
    selected_player = st.multiselect("Select Player Number(s)", player_numbers, default=player_numbers)
    
    # Apply filters
    filtered_df = df[
        (df["Team"].isin(selected_team)) &
        (df["Jahr"].isin(selected_year)) &
        (df["Spielernummer"].isin(selected_player))
    ]
    
    st.write(f"Showing {len(filtered_df)} rows after filtering:")
    st.dataframe(filtered_df, height=400)

# Tab 2: Player Stats with Visualizations
with tab2:
    st.subheader("Player Stats")
    
    # Dropdowns to select a team and player
    st.write("Select a Player:")
    selected_team = st.selectbox("Select Team", teams, key="player_team")
    player_numbers = sorted(df[df["Team"] == selected_team]["Spielernummer"].astype(int).unique())  # Convert to int
    selected_player = st.selectbox("Select Player Number", player_numbers, key="player_number", format_func=lambda x: str(x))
    
    # Filter data for the selected player
    player_filter = filtered_df[
        (filtered_df["Team"] == selected_team) &
        (filtered_df["Spielernummer"] == selected_player)
    ]
    
    # Total events per player (pivot table: years vs events)
    st.write(f"Total Events for Player {selected_player} ({selected_team}):")
    if not player_filter.empty:
        player_summary = player_filter.pivot_table(
            index="Jahr",
            columns="Event",
            values="Anzahl",
            aggfunc="sum",
            fill_value=0
        )
        # Define the desired column order
        desired_order = ["First Down", "Touchdown", "1-Extra-Punkt", "2-Extra-Punkte", "Interception", "Safety (+2)", "Strafe"]
        # Reorder columns based on desired order, keeping any additional columns at the end
        existing_columns = [col for col in desired_order if col in player_summary.columns]
        remaining_columns = [col for col in player_summary.columns if col not in desired_order]
        player_summary = player_summary[existing_columns + remaining_columns]
        # Add a "Total" row
        total = player_summary.sum().to_frame().T
        total.index = ["Total"]
        player_summary = pd.concat([player_summary, total])
        # Style the "Total" row
        styled_summary = player_summary.style.apply(
            lambda x: ["font-weight: bold; background-color: #333333" if x.name == "Total" else "" for _ in x],
            axis=1
        )
        st.dataframe(styled_summary)
    else:
        st.write("No data available for this player.")
    
    # Visualization: Bar chart of events over time
    st.write("Events per Year:")
    event_types = sorted(df["Event"].unique())
    selected_event = st.selectbox("Select Event to Visualize", event_types, key="player_event")
    event_data = player_filter[player_filter["Event"] == selected_event].groupby("Jahr")["Anzahl"].sum().reset_index()
    if not event_data.empty:
        # Convert Jahr to string to treat it as categorical
        event_data["Jahr"] = event_data["Jahr"].astype(str)
        fig = px.bar(
            event_data,
            x="Jahr",
            y="Anzahl",
            title=f"{selected_event} per Year for Player {selected_player} ({selected_team})",
            labels={"Jahr": "Year", "Anzahl": "Count"},
            text="Anzahl"  # Display the count on the bars
        )
        fig.update_traces(textposition="outside")
        # Ensure x-axis is treated as categorical
        fig.update_xaxes(type="category")
        st.plotly_chart(fig)
    else:
        st.write(f"No {selected_event} data available for this player.")

# Tab 3: Team Stats with Visualizations
with tab3:
    st.subheader("Team Stats")
    
    # Dropdown to select a team
    st.write("Select a Team:")
    selected_team_stats = st.selectbox("Select Team", teams, key="team_stats_team")
    
    # Filter data for the selected team
    team_filter = filtered_df[filtered_df["Team"] == selected_team_stats]
    
    # Total events per team (pivot table: years vs events)
    st.write(f"Total Events for {selected_team_stats}:")
    if not team_filter.empty:
        team_summary = team_filter.pivot_table(
            index="Jahr",
            columns="Event",
            values="Anzahl",
            aggfunc="sum",
            fill_value=0
        )
        # Reorder columns based on desired order
        existing_columns = [col for col in desired_order if col in team_summary.columns]
        remaining_columns = [col for col in team_summary.columns if col not in desired_order]
        team_summary = team_summary[existing_columns + remaining_columns]
        # Add a "Total" row
        total = team_summary.sum().to_frame().T
        total.index = ["Total"]
        team_summary = pd.concat([team_summary, total])
        # Style the "Total" row
        styled_summary = team_summary.style.apply(
            lambda x: ["font-weight: bold; background-color: #333333" if x.name == "Total" else "" for _ in x],
            axis=1
        )
        st.dataframe(styled_summary)
    else:
        st.write("No data available for this team.")
    
    # Visualization: Bar chart of events over time
    st.write("Events per Year:")
    selected_team_event = st.selectbox("Select Event to Visualize", event_types, key="team_event")
    event_data = team_filter[team_filter["Event"] == selected_team_event].groupby("Jahr")["Anzahl"].sum().reset_index()
    if not event_data.empty:
        # Convert Jahr to string to treat it as categorical
        event_data["Jahr"] = event_data["Jahr"].astype(str)
        fig = px.bar(
            event_data,
            x="Jahr",
            y="Anzahl",
            title=f"{selected_team_event} per Year for {selected_team_stats}",
            labels={"Jahr": "Year", "Anzahl": "Count"},
            text="Anzahl"  # Display the count on the bars
        )
        fig.update_traces(textposition="outside")
        # Ensure x-axis is treated as categorical
        fig.update_xaxes(type="category")
        st.plotly_chart(fig)
    else:
        st.write(f"No {selected_team_event} data available for this team.")