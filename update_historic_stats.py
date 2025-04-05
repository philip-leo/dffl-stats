import pandas as pd
from config import standardize_dataframe, EXPECTED_COLUMNS

def update_historic_data():
    """Update the historic data file by processing the complete dataset."""
    print("Starting historic data update...")
    try:
        # Read the complete dataset
        print("Reading complete dataset...")
        df = pd.read_csv("dffl_stats.csv", dtype=EXPECTED_COLUMNS)
        
        # Standardize the dataframe
        df = standardize_dataframe(df, is_german=True)
        
        # Filter for years before 2025
        historic_df = df[df['Year'] < 2025].copy()
        
        # Save the processed historic data
        print("\nSaving processed historic data...")
        historic_df.to_csv("dffl_stats_historic.csv", index=False)
        print(f"Saved historic data to dffl_stats_historic.csv with {len(historic_df)} rows")
        print("Columns:", historic_df.columns.tolist())
        
        print("\nHistoric data update completed successfully!")
        return "dffl_stats_historic.csv"
        
    except Exception as e:
        print(f"Error in update_historic_data(): {str(e)}")
        raise

if __name__ == "__main__":
    update_historic_data() 