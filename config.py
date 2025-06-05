import pandas as pd

# Column name mapping from German to English
COLUMN_MAPPING = {
    'Team': 'Team',  # Same in both languages
    'Spielernummer': 'Player Number',
    'Anzahl': 'Count',
    'Event': 'Event',  # Same in both languages
    'Jahr': 'Year',
    # New mappings for detailed stats
    'Gegen': 'Opponent',
    'Spieltag': 'Matchday',
    'Datum': 'Date',
    'stage': 'Stage',
    'standing': 'Standing',
    'scheduled': 'Scheduled Time',
    'created_time': 'Created Time'
}

# Expected column names in English (after translation)
EXPECTED_COLUMNS = {
    'Team': str,
    'Player Number': str,  # Keep as string initially, will be converted to Int64 after cleaning
    'Count': int,
    'Event': str,
    'Year': int,
    # New columns for detailed stats
    'Opponent': str,
    'Matchday': str,
    'Date': str,
    'Stage': str,
    'Standing': str,
    'Scheduled Time': str,
    'Created Time': str
}

def clean_player_number(value):
    """Clean player number values consistently across all scripts."""
    if pd.isna(value):
        return None
    try:
        # Convert to float first to handle decimal format (e.g., "19.0")
        float_value = float(str(value).strip())
        # Convert to integer
        return int(float_value)
    except Exception as e:
        print(f"Error cleaning player number value '{value}': {str(e)}")
        return None

def standardize_dataframe(df, is_german=True):
    """Standardize a dataframe by applying column mapping and data type conversions."""
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Rename columns if the input is in German
    if is_german:
        # Only rename columns that exist in the dataframe
        rename_dict = {k: v for k, v in COLUMN_MAPPING.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
    
    # Clean player numbers if the column exists
    if 'Player Number' in df.columns:
        df['Player Number'] = df['Player Number'].apply(clean_player_number)
        df['Player Number'] = df['Player Number'].astype('Int64')
    
    # Ensure correct data types for columns that exist
    type_conversions = {}
    for col, dtype in EXPECTED_COLUMNS.items():
        if col in df.columns:
            type_conversions[col] = dtype
    
    # Apply type conversions only for columns that exist
    if type_conversions:
        df = df.astype(type_conversions)
    
    return df