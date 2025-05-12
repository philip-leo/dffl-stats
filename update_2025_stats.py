from playwright.sync_api import sync_playwright
import time
import pandas as pd
import base64
from io import StringIO
from config import standardize_dataframe

# Column name mapping from German to English
COLUMN_MAPPING = {
    'Team': 'Team',  # Same in both languages
    'Spielernummer': 'Player Number',
    'Anzahl': 'Count',
    'Event': 'Event',  # Same in both languages
    'Jahr': 'Year'
}

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

def process_downloaded_data(csv_data):
    """Process the downloaded CSV data to ensure consistent English column names and data types."""
    # Read the CSV data
    df = pd.read_csv(StringIO(csv_data))
    
    # Standardize the dataframe (convert German to English, clean data types)
    df = standardize_dataframe(df, is_german=True)
    
    return df

def update_2025_data():
    print("Starting weekly update of 2025 data...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # Navigate to the page
            print("Navigating to DFFL site...")
            page.goto("https://www.5erdffl.de/player-stats/", timeout=90000)
            
            # Try to handle cookie banner if present
            try:
                for selector in [
                    'button[data-cookiefirst-action="accept"]',
                    '#cookie-law-info-bar button',
                    '[aria-label="Accept cookies"]',
                    'button:has-text("Accept")',
                    'button:has-text("Akzeptieren")'
                ]:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).click()
                        print(f"Clicked cookie banner with selector: {selector}")
                        break
            except Exception as e:
                print(f"Note: Could not handle cookie banner: {e}")

            # Wait for table and DataTables to initialize
            print("Waiting for table and DataTables to initialize...")
            page.wait_for_selector("#table_1")
            page.wait_for_function("typeof jQuery !== 'undefined' && typeof jQuery('#table_1').DataTable === 'function'")
            
            # Apply filter using DataTables API directly
            print("\nApplying year filter using DataTables API...")
            page.evaluate("""() => {
                const table = jQuery('#table_1').DataTable();
                table.page.len(-1).draw();
                const yearColumnIdx = table.columns().indexes().toArray()
                    .find(idx => table.column(idx).header().textContent.trim() === 'Jahr');
                if (yearColumnIdx !== undefined) {
                    table.search('').columns().search('').draw();
                    table.column(yearColumnIdx).search('2025').draw();
                }
            }""")
            
            # Wait for filtering to complete and check row count
            time.sleep(2)
            debug_info = page.evaluate("""() => {
                const table = jQuery('#table_1').DataTable();
                const yearColumnIdx = table.columns().indexes().toArray()
                    .find(idx => table.column(idx).header().textContent.trim() === 'Jahr');
                return {
                    totalRows: table.rows().count(),
                    filteredRows: table.rows({ search: 'applied' }).count(),
                    yearColumnIndex: yearColumnIdx,
                    currentSearch: table.column(yearColumnIdx).search()[0],
                    sampleData: table.rows({ search: 'applied' }).data().slice(0, 5).toArray(),
                    allSample: table.rows().data().slice(0, 5).toArray()
                };
            }""")
            print("\nDebug information:")
            print(f"Total rows in table: {debug_info['totalRows']}")
            print(f"Filtered rows: {debug_info['filteredRows']}")
            print(f"Year column index: {debug_info['yearColumnIndex']}")
            print(f"Current search: {debug_info['currentSearch']}")
            print("Sample filtered data:", debug_info['sampleData'])
            if debug_info['filteredRows'] < 50:
                print("WARNING: Filtered row count is unexpectedly low! Printing first few unfiltered rows for diagnosis:")
                print(debug_info['allSample'])
            
            # Click the CSV download button and get the data
            print("\nGetting CSV data...")
            csv_data = page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const table = jQuery('#table_1').DataTable();
                        const csvData = table.buttons.exportData({
                            format: {
                                header: function(data, columnIdx) {
                                    return table.column(columnIdx).header().textContent.trim();
                                }
                            }
                        });
                        
                        const headers = csvData.header.join(',');
                        const rows = csvData.body.map(row => row.join(','));
                        const csv = headers + '\\n' + rows.join('\\n');
                        resolve(csv);
                    });
                }
            """)
            
            # Process the downloaded data
            print("\nProcessing downloaded data...")
            df = process_downloaded_data(csv_data)
            
            # Save the processed CSV data
            print("\nSaving processed data...")
            df.to_csv("dffl_stats_2025.csv", index=False)
            print(f"Saved updated 2025 data to dffl_stats_2025.csv with {len(df)} rows")
            print("Columns:", df.columns.tolist())
            
            browser.close()
            print("\nWeekly update completed successfully!")
            return "dffl_stats_2025.csv"
    except Exception as e:
        print(f"Error in update_2025_data(): {str(e)}")
        raise

if __name__ == "__main__":
    update_2025_data() 