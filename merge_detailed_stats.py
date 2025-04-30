import pandas as pd
import os
from config import standardize_dataframe

def merge_historic_files():
    """Merge the historic detailed stats files (2022-2024) into a single file."""
    print("Loading historic files...")
    
    # List of historic files in chronological order (newest to oldest)
    historic_files = [
        "Player Stats_detail (1).csv",  # 2024
        "Player Stats_detail (2).csv",  # 2023
        "Player Stats_detail (3).csv"   # 2022
    ]
    
    # Initialize an empty list to store dataframes
    dfs = []
    
    # Load and process each file
    for file in historic_files:
        if os.path.exists(file):
            print(f"Processing {file}...")
            df = pd.read_csv(file)
            dfs.append(df)
        else:
            print(f"Warning: {file} not found")
    
    if not dfs:
        print("No historic files found to merge")
        return
    
    # Concatenate all dataframes
    print("Merging historic files...")
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Save the merged file
    output_file = "dffl_stats_detail_historic.csv"
    merged_df.to_csv(output_file, index=False)
    print(f"Saved merged historic data to {output_file}")
    print(f"Total rows in historic data: {len(merged_df)}")

def prepare_2025_file():
    """Prepare the 2025 detailed stats file."""
    print("\nPreparing 2025 file...")
    input_file = "Player Stats_detail.csv"
    output_file = "dffl_stats_detail_2025.csv"
    
    if os.path.exists(input_file):
        df = pd.read_csv(input_file)
        df.to_csv(output_file, index=False)
        print(f"Saved 2025 data to {output_file}")
        print(f"Total rows in 2025 data: {len(df)}")
    else:
        print(f"Warning: {input_file} not found")

if __name__ == "__main__":
    merge_historic_files()
    prepare_2025_file()
    print("\nProcess completed!") 