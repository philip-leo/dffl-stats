from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import pandas as pd
import base64
import traceback
from io import StringIO
from config import standardize_dataframe

# Column name mapping from German to English
COLUMN_MAPPING = {
    'Team': 'Team',  # Same in both languages
    'Spielernummer': 'Player Number',
    'Anzahl': 'Count',
    'Event': 'Event',  # Same in both languages
    'Jahr': 'Year',
    'Gegen': 'Against',
    'Spieltag': 'Game Day',
    'Datum': 'Date',
    'stage': 'Stage',
    'standing': 'Standing',
    'scheduled': 'Scheduled',
    'created_time': 'Created Time'
}

def log_message(message):
    """Helper function to print timestamps with messages"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Debug function removed as it's no longer needed

def wait_for_table_data(page, timeout=60000, table_id='table_1'):
    """Wait for the table to be populated with data"""
    log_message(f"Waiting for {table_id} data to load...")
    start_time = time.time()
    
    while time.time() - start_time < timeout / 1000:
        try:
            # Check for loading indicators
            loading = page.evaluate(f"""(tableId) => {{
                // Check for common loading indicators
                const loadingIndicators = [
                    document.querySelector('.dataTables_processing'),
                    document.querySelector('.loading'),
                    document.querySelector('.spinner'),
                    document.querySelector('.loader'),
                    document.querySelector('.dataTables_empty')
                ].filter(el => el && el.offsetParent !== null);
                
                // Check for loading text in any div
                const loadingDivs = Array.from(document.querySelectorAll('div'))
                    .filter(div => {{
                        const text = div.textContent.trim();
                        return text === 'Loading...' || text === 'Lade...' || text === 'Loading' || text === 'Laden';
                    }});
                
                return {{
                    isLoading: loadingIndicators.length > 0 || loadingDivs.length > 0,
                    hasNoData: document.querySelector('.dataTables_empty') !== null
                }};
            }}""", table_id)
            
            # Check if we have actual data rows
            has_data = page.evaluate(f"""(tableId) => {{
                const rows = document.querySelectorAll('#' + tableId + ' tbody tr');
                if (rows.length === 0) return false;
                
                // Check if any row has content
                for (const row of rows) {{
                    const text = row.textContent.trim();
                    if (text && 
                        !text.includes('No data available') && 
                        !text.includes('Keine Daten verfügbar') &&
                        !text.includes('Loading...') &&
                        !text.includes('Lade...')) {{
                        return true;
                    }}
                }}
                return false;
            }}""", table_id)
            
            if has_data:
                log_message(f"{table_id} data loaded successfully")
                return True
                
            # If we have no data but also no loading indicators, we might be done
            if not loading['isLoading'] and not loading['hasNoData'] and page.evaluate("""() => {
                return document.readyState === 'complete';
            }"""):
                log_message(f"Page fully loaded but no {table_id} data found")
                return False
                
        except Exception as e:
            log_message(f"Error checking {table_id} status: {str(e)}")
        
        time.sleep(1)  # Check every second
    
    log_message(f"Timed out waiting for {table_id} data")
    return False

def handle_cookie_banner(page):
    """Handle cookie consent banner if present"""
    try:
        # List of possible cookie banner selectors
        cookie_selectors = [
            'button[data-cookiefirst-action="accept"]',
            '#cookie-law-info-bar button',
            '[aria-label*="cookie" i] button',
            'button:has-text("Accept")',
            'button:has-text("Akzeptieren")',
            '.fc-cta-consent',
            '#didomi-notice-agree-button',
            '.didomi-consent-popup-agree-button',
            '.cookie-consent-button',
            '#cookie-consent-accept',
            '#accept-cookies',
            '.accept-cookies',
            '.js-accept-cookies',
            '.cookie-banner-accept',
            '.cookie-consent-accept',
            '.cookie-accept',
            '.cookie-ok',
            '.cookie-agree',
            '.cookie-allow',
            '.cookie-close',
            '.cookie-button',
            '.cookie-btn'
        ]
        
        for selector in cookie_selectors:
            try:
                if page.is_visible(selector, timeout=1000):
                    page.click(selector)
                    log_message(f"Clicked cookie banner with selector: {selector}")
                    time.sleep(1)  # Wait for the banner to disappear
                    return True
            except Exception as e:
                log_message(f"Tried cookie selector {selector}: {str(e)}")
                continue
                
        log_message("No cookie banner found with standard selectors")
        return False
        
    except Exception as e:
        log_message(f"Error in handle_cookie_banner: {str(e)}")
        return False

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
        log_message(f"Error cleaning player number value '{value}': {str(e)}")
        return None

def process_downloaded_data(csv_data):
    """Process the downloaded CSV data to ensure consistent English column names and data types."""
    try:
        # Read the CSV data
        df = pd.read_csv(StringIO(csv_data))
        
        # Standardize the dataframe
        df = standardize_dataframe(df, is_german=True)
        
        return df
    except Exception as e:
        log_message(f"Error processing downloaded data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def extract_table_data(page, table_id, year_filter='2025', output_file=None):
    """Generic function to extract data from a table
    
    Args:
        page: Playwright page object
        table_id: ID of the table to extract data from (e.g., 'table_1')
        year_filter: Year to filter for (default: '2025')
        output_file: Path to save the extracted data (optional)
        
    Returns:
        DataFrame with the extracted data, or None if extraction failed
    """
    log_message(f"Extracting data from {table_id}...")
    
    # Method 1: Try DataTables API first
    try:
        log_message(f"Trying DataTables API extraction for {table_id}...")
        csv_data = page.evaluate(f"""
            (tableId) => {{
                return new Promise((resolve) => {{
                    try {{
                        if (window.jQuery && window.jQuery.fn.DataTable) {{
                            const table = jQuery('#' + tableId).DataTable();
                            const csvData = table.buttons.exportData({{
                                format: {{
                                    header: function(data, columnIdx) {{
                                        return table.column(columnIdx).header().textContent.trim();
                                    }}
                                }}
                            }});
                            
                            const headers = csvData.header.join(',');
                            const rows = csvData.body.map(row => row.join(','));
                            const csv = headers + '\n' + rows.join('\n');
                            resolve(csv);
                        }} else {{
                            resolve(null);
                        }}
                    }} catch (e) {{
                        console.error('Error extracting via DataTables:', e);
                        resolve(null);
                    }}
                }});
            }}
        """, table_id)
        
        if csv_data:
            # Process the downloaded data
            log_message(f"Processing data from {table_id} DataTables API...")
            df = process_downloaded_data(csv_data)
            
            if not df.empty:
                # Filter for the specified year
                year_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['jahr', 'year', 'datum', 'date'])]
                
                if year_columns:
                    year_col = year_columns[0]
                    log_message(f"Found year column: {year_col}")
                    
                    # Filter for the specified year
                    df_filtered = df[df[year_col].astype(str).str.contains(year_filter)]
                    
                    if not df_filtered.empty:
                        log_message(f"Found {len(df_filtered)} rows for {year_filter}")
                        
                        # Save to file if specified
                        if output_file:
                            df_filtered.to_csv(output_file, index=False)
                            log_message(f"Saved {len(df_filtered)} rows to {output_file}")
                            log_message(f"Columns: {df_filtered.columns.tolist()}")
                        
                        return df_filtered
                    else:
                        log_message(f"No {year_filter} data found in the extracted data")
                else:
                    log_message(f"No year column found in {table_id}")
                    
                    # If we can't find a year column, just return all data
                    if output_file:
                        df.to_csv(output_file, index=False)
                        log_message(f"Saved {len(df)} rows to {output_file} (no year filtering)")
                    
                    return df
    except Exception as e:
        log_message(f"Error with {table_id} DataTables API extraction: {str(e)}")
    
    # Method 2: Try direct DOM extraction
    try:
        log_message(f"Trying direct DOM extraction for {table_id}...")
        
        # Get all available column headers
        headers = page.evaluate(f"""
            (tableId) => {{
                return Array.from(document.querySelectorAll('#' + tableId + ' thead th')).map(th => th.innerText.trim());
            }}
        """, table_id)
        
        # Extract all data rows at once (since we're using 'All' option for rows per page)
        log_message(f"Extracting all data from {table_id}...")
        
        # Try to get the total number of rows in the filtered table
        total_rows = page.evaluate(f"""
            (tableId) => {{
                try {{
                    // Try to get the info from the DataTables API
                    if (window.jQuery && jQuery('#' + tableId).DataTable) {{
                        const table = jQuery('#' + tableId).DataTable();
                        return table.page.info().recordsDisplay;
                    }}
                    
                    // Fallback: try to get from the info display
                    const infoElement = document.querySelector('#' + tableId + '_info');
                    if (infoElement) {{
                        const infoText = infoElement.textContent;
                        // Use a safer regex pattern with double backslashes for digits
                        const match = infoText.match(/([0-9]+(?:,[0-9]+)*) Einträgen/i);
                        if (match) {{
                            return parseInt(match[1].replace(/,/g, ''));
                        }}
                    }}
                }} catch (e) {{
                    console.error('Error getting total rows:', e);
                }}
                return null;
            }}
        """, table_id)
        
        log_message(f"Total filtered rows in {table_id}: {total_rows if total_rows is not None else 'unknown'}")
        
        # For large tables, especially table_2 with 15,000+ rows, we need a different approach
        if table_id == 'table_2' and (total_rows is None or total_rows > 1000):
            log_message(f"Using special extraction for large table {table_id}")
            
            # Get data using DataTables API directly with proper error handling
            all_data = page.evaluate(f"""
                (params) => {{
                    return new Promise((resolve) => {{
                        try {{
                            const tableId = params.tableId;
                            const headers = params.headers;
                            const rows = [];
                            
                            // Try to use DataTables API directly
                            if (window.jQuery && jQuery('#' + tableId).DataTable) {{
                                const table = jQuery('#' + tableId).DataTable();
                                const totalRows = table.page.info().recordsDisplay;
                                console.log('Total rows in DataTable: ' + totalRows);
                                
                                // Get all data at once
                                const allData = table.rows({{'search': 'applied'}}).data();
                                console.log('Retrieved ' + allData.length + ' rows from DataTable API');
                                
                                // Convert to array of objects
                                for (let i = 0; i < allData.length; i++) {{
                                    const rowData = {{}};
                                    for (let j = 0; j < headers.length; j++) {{
                                        if (headers[j] && allData[i][j] !== undefined) {{
                                            rowData[headers[j]] = allData[i][j];
                                        }}
                                    }}
                                    if (Object.keys(rowData).length > 0) {{
                                        rows.push(rowData);
                                    }}
                                }}
                                
                                resolve(rows);
                                return;
                            }}
                            
                            // Fallback to DOM extraction for visible rows
                            const tableRows = document.querySelectorAll('#' + tableId + ' tbody tr:not(.dataTables_empty)');
                            console.log('Fallback: Found ' + tableRows.length + ' visible rows in table ' + tableId);
                            
                            tableRows.forEach(row => {{
                                const rowData = {{}};
                                const cells = row.querySelectorAll('td');
                                
                                cells.forEach((cell, index) => {{
                                    if (headers[index]) {{
                                        rowData[headers[index]] = cell.innerText.trim();
                                    }}
                                }});
                                
                                if (Object.keys(rowData).length > 0) {{
                                    rows.push(rowData);
                                }}
                            }});
                            
                            resolve(rows);
                        }} catch (e) {{
                            console.error('Error in data extraction:', e);
                            // Return whatever we have
                            resolve([]);
                        }}
                    }});
                }}
            """, {'tableId': table_id, 'headers': headers})
        else:
            # Standard approach for smaller tables
            all_data = page.evaluate(f"""
                (params) => {{
                    const tableId = params.tableId;
                    const headers = params.headers;
                    const rows = [];
                    const tableRows = document.querySelectorAll('#' + tableId + ' tbody tr:not(.dataTables_empty)');
                    
                    console.log('Found ' + tableRows.length + ' rows in table ' + tableId);
                    
                    tableRows.forEach(row => {{
                        const rowData = {{}};
                        const cells = row.querySelectorAll('td');
                        
                        cells.forEach((cell, index) => {{
                            if (headers[index]) {{
                                rowData[headers[index]] = cell.innerText.trim();
                            }}
                        }});
                        
                        if (Object.keys(rowData).length > 0) {{
                            rows.push(rowData);
                        }}
                    }});
                    
                    return rows;
                }}
            """, {'tableId': table_id, 'headers': headers})
        
        log_message(f"Extracted {len(all_data)} rows from {table_id}")

        
        if all_data:
            df = pd.DataFrame(all_data)
            log_message(f"Extracted {len(df)} total rows from {table_id} via DOM")
            
            if not df.empty:
                # Try to find year column (case insensitive)
                year_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['jahr', 'year', 'datum', 'date'])]
                
                if year_columns:
                    year_col = year_columns[0]
                    log_message(f"Found year column: {year_col}")
                    
                    # Get unique years in the data
                    unique_years = df[year_col].unique()
                    log_message(f"Available years in data: {', '.join(map(str, unique_years))}")
                    
                    # Filter for specified year data
                    df_year = df[df[year_col].astype(str).str.contains(year_filter)]
                    
                    if not df_year.empty:
                        # Process the data through the standardization function
                        processed_df = standardize_dataframe(df_year, is_german=True)
                        
                        # Save the processed data
                        if output_file:
                            processed_df.to_csv(output_file, index=False)
                            log_message(f"Saved {len(processed_df)} rows of processed {year_filter} data to {output_file}")
                        return processed_df
                    else:
                        log_message(f"No {year_filter} data found in the extracted data. Using most recent data instead.")
                        # For testing purposes, use the most recent data available
                        # In production, this would filter for the most recent year
                        processed_df = standardize_dataframe(df, is_german=True)
                        
                        # Save the processed data
                        if output_file:
                            processed_df.to_csv(output_file, index=False)
                            log_message(f"Saved {len(processed_df)} rows of available data to {output_file}")
                        return processed_df
                else:
                    # If no year column found, just use all the data
                    log_message(f"No year column found. Using all available data.")
                    processed_df = standardize_dataframe(df, is_german=True)
                    
                    if output_file:
                        processed_df.to_csv(output_file, index=False)
                        log_message(f"Saved {len(processed_df)} rows to {output_file} (no year filtering)")
                    
                    return processed_df
    except Exception as e:
        log_message(f"Error with {table_id} DOM extraction: {str(e)}")
        log_message(traceback.format_exc())
    
    log_message(f"All data extraction methods failed for {table_id}")
    return None

def update_2025_data():
    log_message("Starting weekly update of 2025 data...")
    try:
        with sync_playwright() as p:
            # Launch browser with more options
            log_message("Launching browser...")
            browser = p.chromium.launch(
                headless=True,  # Set to True for production
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create a new browser context with viewport and user agent
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                java_script_enabled=True,
                bypass_csp=True,
                ignore_https_errors=True
            )
            
            # Enable request/response logging
            def handle_console(msg):
                log_message(f"Console: {msg.text}")
            
            # Create a new page
            page = context.new_page()
            page.on("console", handle_console)
            
            # Navigate to the page with a longer timeout
            log_message("Navigating to DFFL site...")
            page.goto(
                "https://www.5erdffl.de/player-stats/", 
                timeout=120000, 
                wait_until="domcontentloaded"
            )
            
            # Handle cookie banner
            log_message("Handling cookie banner...")
            handle_cookie_banner(page)
            
            # Process main stats table (table_1)
            log_message("Processing main stats table (table_1)...")
            
            # Wait for the main table to be visible
            try:
                page.wait_for_selector("#table_1", timeout=30000)
                log_message("Main table found on the page")
            except PlaywrightTimeoutError:
                log_message("Main table not found within timeout")
                raise
            
            # Wait for main table data to load
            if not wait_for_table_data(page, timeout=60000, table_id='table_1'):
                log_message("Failed to load main table data")
                raise Exception("Main table data did not load")
            
            # First, try to set the table to show all entries
            try:
                log_message("Setting main table to show all entries...")
                # Try to select 'All' from the dropdown
                page.evaluate("""() => {
                    try {
                        // Try to find and click the dropdown
                        const lengthDropdown = document.querySelector('#table_1_length .btn.dropdown-toggle');
                        if (lengthDropdown) {
                            lengthDropdown.click();
                            // Wait a bit for dropdown to open
                            setTimeout(() => {
                                // Find and click the 'All' option
                                const allOption = Array.from(document.querySelectorAll('#table_1_length .dropdown-menu li'))
                                    .find(li => li.textContent.trim() === 'All');
                                if (allOption) {
                                    allOption.querySelector('a').click();
                                    return true;
                                }
                            }, 1000);
                        }
                    } catch (e) {
                        console.error('Error selecting All rows:', e);
                    }
                }""")
                
                # Also try the direct select approach
                page.select_option('select[name="table_1_length"]', value="-1")
                log_message("Set main table length to show all rows")
                time.sleep(10)  # Wait for table to update
            except Exception as e:
                log_message(f"Error setting main table length: {str(e)}")
            
            # Apply year filter for 2025
            try:
                log_message("Setting year filter to 2025...")
                # Try to find and use the year filter input
                year_filter_set = page.evaluate("""() => {
                    try {
                        // Look for year filter input
                        const yearFilter = document.querySelector('input[placeholder="Jahr"]');
                        if (yearFilter) {
                            yearFilter.value = '2025';
                            yearFilter.dispatchEvent(new Event('input', { bubbles: true }));
                            yearFilter.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                        return false;
                    } catch (e) {
                        console.error('Error setting year filter:', e);
                        return false;
                    }
                }""")
                
                if year_filter_set:
                    log_message("Successfully set year filter to 2025")
                    # Give time for the filter to apply
                    log_message("Waiting for year filter to apply...")
                    time.sleep(30)  # Increased wait time
            except Exception as e:
                log_message(f"Error setting year filter: {str(e)}")
            
            # Wait for table data to load after filtering
            if not wait_for_table_data(page, timeout=60000, table_id='table_1'):
                log_message("Warning: Main table data may not have loaded completely")
                # Continue anyway
            
            # Extract main stats data using our generic function
            main_stats_df = extract_table_data(page, 'table_1', year_filter='2025', output_file='dffl_stats_2025.csv')
            
            if main_stats_df is None or main_stats_df.empty:
                log_message("Failed to extract main stats data")
                raise Exception("Failed to extract main stats data")
            
            log_message(f"Successfully extracted {len(main_stats_df)} rows of main stats data")
            
            # Now process the detail stats table (table_2)
            log_message("Processing detail stats table (table_2)...")
            
            # Wait for the detail table to be visible
            try:
                page.wait_for_selector("#table_2", timeout=30000)
                log_message("Detail table found on the page")
            except PlaywrightTimeoutError:
                log_message("Detail table not found within timeout")
                # Continue with main data only
                log_message("Warning: Detail table not found, but continuing since main stats were successful")
                browser.close()
                return
            
            # Wait for detail table data to load initially
            if not wait_for_table_data(page, timeout=60000, table_id='table_2'):
                log_message("Warning: Detail table initial data may not have loaded completely")
                # Continue anyway
            
            # Filtering detail table for 2025 data
            log_message("Filtering detail table for 2025 data...")
            
            # Try to set Datum filter to 2025
            try:
                # Try to find and use the Datum filter input
                datum_filter_set = page.evaluate("""() => {
                    try {
                        // Look for Datum filter input
                        const datumFilter = document.querySelector('input[placeholder=\"Datum\"]');
                        if (datumFilter) {
                            datumFilter.value = '2025';
                            datumFilter.dispatchEvent(new Event('input', { bubbles: true }));
                            datumFilter.dispatchEvent(new Event('change', { bubbles: true }));
                            datumFilter.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter' }));
                            return true;
                        }
                        return false;
                    } catch (e) {
                        console.error('Error setting Datum filter:', e);
                        return false;
                    }
                }""")
                
                if datum_filter_set:
                    log_message("Successfully set Datum filter to 2025")
                    # Give more time for the filter to apply
                    log_message("Waiting for Datum filter to apply...")
                    time.sleep(30)  # Increased wait time
            except Exception as e:
                log_message(f"Error setting Datum filter: {str(e)}")
            

            # Wait for detail table data to load after filtering
            if not wait_for_table_data(page, timeout=60000, table_id='table_2'):
                log_message("Warning: Detail table data may not have loaded completely")
                # Continue anyway

            # Try to set the table to show all entries for the detail table
            try:
                log_message("Setting detail table to show ALL entries...")
                
                # First, let's verify the current state of the table
                table_info_before = page.evaluate("""() => {
                    const infoElement = document.querySelector('#table_2_info');
                    if (infoElement) {
                        return infoElement.textContent;
                    }
                    return null;
                }""")
                
                log_message(f"Table info before setting All: {table_info_before}")
                
                # Try multiple approaches to select 'All'
                # Approach 1: Use the dropdown UI
                page.evaluate("""() => {
                    try {
                        // Try to find and click the dropdown
                        const lengthDropdown = document.querySelector('#table_2_length .btn.dropdown-toggle');
                        if (lengthDropdown) {
                            lengthDropdown.click();
                            console.log('Clicked length dropdown');
                            
                            // Wait for dropdown to open
                            setTimeout(() => {
                                // Find and click the 'All' option
                                const allOptions = Array.from(document.querySelectorAll('#table_2_length .dropdown-menu li'));
                                console.log('Found ' + allOptions.length + ' dropdown options');
                                
                                const allOption = allOptions.find(li => li.textContent.trim() === 'All');
                                if (allOption) {
                                    console.log('Found All option, clicking it');
                                    allOption.querySelector('a').click();
                                } else {
                                    console.log('All option not found. Available options: ' + 
                                        allOptions.map(li => li.textContent.trim()).join(', '));
                                }
                            }, 1000);
                        } else {
                            console.log('Length dropdown not found');
                        }
                    } catch (e) {
                        console.error('Error selecting All rows:', e);
                    }
                }""")
                
                # Wait for dropdown interaction
                time.sleep(3)
                
                # Approach 2: Direct select option
                try:
                    page.select_option('select[name="table_2_length"]', value="-1")
                    log_message("Used select_option to set All rows")
                except Exception as e:
                    log_message(f"Error with select_option: {str(e)}")
                
                # Approach 3: Use DataTables API directly
                page.evaluate("""() => {
                    try {
                        if (window.jQuery && jQuery('#table_2').DataTable) {
                            const table = jQuery('#table_2').DataTable();
                            table.page.len(-1).draw();
                            console.log('Set page length to All via DataTables API');
                            return true;
                        }
                    } catch (e) {
                        console.error('Error setting All rows via API:', e);
                    }
                    return false;
                }""")
                
                log_message("Set detail table length to show all rows")
                
                # Wait for table to update - this might take longer for a large table
                time.sleep(30)
                
                # Verify the change took effect
                table_info_after = page.evaluate("""() => {
                    const infoElement = document.querySelector('#table_2_info');
                    if (infoElement) {
                        return infoElement.textContent;
                    }
                    return null;
                }""")
                
                log_message(f"Table info after setting All: {table_info_after}")
                
                # Check if we're showing all rows now
                if "all" in table_info_after.lower() or "alle" in table_info_after.lower():
                    log_message("Successfully set to show ALL rows")
                else:
                    log_message("Warning: May not have successfully set to show ALL rows")
                    
            except Exception as e:
                log_message(f"Error setting detail table length: {str(e)}")
            
            # Wait for the table to fully update after filtering and setting to show all rows
            log_message("Waiting for detail table to fully update after filtering and showing all rows...")
            log_message("This may take a while for a large table with 15,000+ rows")
            time.sleep(60)  # Increased wait time to ensure all data loads
            
            # Proceed with data extraction after filtering
            log_message("Extracting detail table data...")
            
            # Try to get the total number of rows in the filtered table
            try:
                # Get the current table info
                table_info = page.evaluate("""() => {
                    const infoElement = document.querySelector('#table_2_info');
                    if (infoElement) {
                        const infoText = infoElement.textContent;
                        // Try to extract total entries
                        let totalEntries = 0;
                        
                        // Pattern for "Showing all X entries"
                        const allPattern = /([0-9]+(?:[.,][0-9]+)*) Eintr[äa]gen/i;
                        const allMatch = infoText.match(allPattern);
                        
                        // Pattern for "Showing X to Y of Z entries"
                        const rangePattern = /[0-9]+ bis [0-9]+ von ([0-9]+(?:[.,][0-9]+)*) Eintr[äa]gen/i;
                        const rangeMatch = infoText.match(rangePattern);
                        
                        // Pattern for filtered entries
                        const filteredPattern = /\\(gefiltert von ([0-9]+(?:[.,][0-9]+)*) Eintr[äa]gen\\)/i;
                        const filteredMatch = infoText.match(filteredPattern);
                        
                        if (allMatch) {
                            totalEntries = parseInt(allMatch[1].replace(/[,.]/g, ''));
                        } else if (rangeMatch) {
                            totalEntries = parseInt(rangeMatch[1].replace(/[,.]/g, ''));
                        }
                        
                        let totalBeforeFilter = 0;
                        if (filteredMatch) {
                            totalBeforeFilter = parseInt(filteredMatch[1].replace(/[,.]/g, ''));
                        }
                        
                        return {
                            text: infoText,
                            totalEntries: totalEntries,
                            totalBeforeFilter: totalBeforeFilter,
                            isShowingAll: infoText.toLowerCase().includes('all') || 
                                          infoText.toLowerCase().includes('alle')
                        };
                    }
                    return { text: 'Unknown', totalEntries: 0, totalBeforeFilter: 0, isShowingAll: false };
                }""")
                
                log_message(f"Table info: {table_info.get('text', 'Unknown')}")
                log_message(f"Total entries: {table_info.get('totalEntries', 0)}")
                log_message(f"Total before filtering: {table_info.get('totalBeforeFilter', 0)}")
                log_message(f"Is showing all rows: {table_info.get('isShowingAll', False)}")
                
                # Get the expected number of rows
                expected_rows = table_info.get('totalEntries', 0)
                
                # Now extract all data at once since we're showing all rows
                log_message("Extracting all rows from the detail table...")
                
                # First, try to use the DataTables API to get all data
                try:
                    log_message("Trying to extract data using DataTables API...")
                    all_data = page.evaluate("""() => {
                        try {
                            if (window.jQuery && jQuery('#table_2').DataTable) {
                                const table = jQuery('#table_2').DataTable();
                                const data = table.rows({search: 'applied'}).data();
                                console.log('Found ' + data.length + ' rows via DataTables API');
                                
                                // Convert to array of objects
                                const headers = Array.from(document.querySelectorAll('#table_2 thead th')).map(th => th.innerText.trim());
                                const result = [];
                                
                                for (let i = 0; i < data.length; i++) {
                                    const row = {};
                                    for (let j = 0; j < headers.length; j++) {
                                        if (headers[j]) {
                                            row[headers[j]] = data[i][j] || '';
                                        }
                                    }
                                    result.push(row);
                                }
                                
                                return result;
                            }
                            return null;
                        } catch (e) {
                            console.error('Error extracting via DataTables API:', e);
                            return null;
                        }
                    }""")
                    
                    if all_data and len(all_data) > 0:
                        log_message(f"Successfully extracted {len(all_data)} rows using DataTables API")
                    else:
                        log_message("DataTables API extraction returned no data or failed")
                        all_data = None
                except Exception as e:
                    log_message(f"Error with DataTables API extraction: {str(e)}")
                    all_data = None
                
                # If DataTables API failed, try direct DOM extraction
                if all_data is None:
                    log_message("Falling back to DOM extraction...")
                    
                    # Get column headers
                    headers = page.evaluate("""
                        () => {
                            return Array.from(document.querySelectorAll('#table_2 thead th')).map(th => th.innerText.trim());
                        }
                    """)
                    
                    # Extract all visible rows from the DOM
                    all_data = page.evaluate("""
                        (headers) => {
                            const rows = [];
                            const tableRows = document.querySelectorAll('#table_2 tbody tr:not(.dataTables_empty)');
                            
                            console.log('Found ' + tableRows.length + ' rows in DOM');
                            
                            tableRows.forEach(row => {
                                const rowData = {};
                                const cells = row.querySelectorAll('td');
                                
                                cells.forEach((cell, index) => {
                                    if (headers[index]) {
                                        rowData[headers[index]] = cell.innerText.trim();
                                    }
                                });
                                
                                if (Object.keys(rowData).length > 0) {
                                    rows.push(rowData);
                                }
                            });
                            
                            return rows;
                        }
                    """, headers)
                    
                    log_message(f"Extracted {len(all_data)} rows from DOM")
                
                # Check if we got the expected number of rows
                if expected_rows > 0 and len(all_data) < expected_rows:
                    log_message(f"Warning: Expected {expected_rows} rows but only extracted {len(all_data)} rows")
                    
                    # If we're showing all rows but didn't get all data, the table might be using virtualization
                    if table_info.get('isShowingAll', False):
                        log_message("The table appears to be using virtualization or lazy loading")
                        log_message("Only the visible rows are in the DOM even with 'All' selected")
                
                # Convert to DataFrame and save
                if all_data and len(all_data) > 0:
                    detail_stats_df = pd.DataFrame(all_data)
                    
                    # Filter for 2025 data (should already be filtered, but just to be safe)
                    year_columns = [col for col in detail_stats_df.columns if any(x in str(col).lower() for x in ['jahr', 'year', 'datum', 'date'])]
                    if year_columns:
                        year_col = year_columns[0]
                        log_message(f"Found year column: {year_col}")
                        log_message(f"Available years in data: {detail_stats_df[year_col].unique()}")
                        detail_stats_df = detail_stats_df[detail_stats_df[year_col].astype(str).str.contains('2025')]
                    
                    # Process the data through standardization
                    processed_df = standardize_dataframe(detail_stats_df, is_german=True)
                    
                    # Save to CSV
                    processed_df.to_csv('dffl_stats_detail_2025.csv', index=False)
                    log_message(f"Saved {len(processed_df)} rows of processed 2025 data to dffl_stats_detail_2025.csv")
                else:
                    log_message("No detail data collected")
                    # Fall back to regular extraction method
                    detail_stats_df = extract_table_data(page, 'table_2', year_filter='2025', output_file='dffl_stats_detail_2025.csv')
            except Exception as e:
                log_message(f"Error during detail table extraction: {str(e)}")
                # Fall back to regular extraction method
                detail_stats_df = extract_table_data(page, 'table_2', year_filter='2025', output_file='dffl_stats_detail_2025.csv')
            
            if detail_stats_df is None or detail_stats_df.empty:
                log_message("Warning: Failed to extract detail stats data, but continuing since main stats were successful")
            else:
                log_message(f"Successfully extracted {len(detail_stats_df)} rows of detail stats data")
            
            # Close the browser
            browser.close()
            log_message("Browser closed")
            
            # Return success if at least the main stats were extracted successfully
            return True
    except Exception as e:
        log_message(f"Error updating 2025 data: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_2025_data() 