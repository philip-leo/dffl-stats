import pandas as pd

# Column name mapping from German to English
COLUMN_MAPPING = {
    'Team': 'Team',  # Same in both languages
    'Spielernummer': 'Player Number',
    'Anzahl': 'Count',
    'Event': 'Event',  # Same in both languages
    'Jahr': 'Year'
}

# Expected column names in English (after translation)
EXPECTED_COLUMNS = {
    'Team': str,
    'Player Number': str,  # Keep as string initially, will be converted to Int64 after cleaning
    'Count': int,
    'Event': str,
    'Year': int
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
        df = df.rename(columns=COLUMN_MAPPING)
    
    # Clean player numbers
    df['Player Number'] = df['Player Number'].apply(clean_player_number)
    df['Player Number'] = df['Player Number'].astype('Int64')
    
    # Ensure correct data types for other columns
    df = df.astype({
        'Team': str,
        'Count': int,
        'Event': str,
        'Year': int
    })
    
    return df 