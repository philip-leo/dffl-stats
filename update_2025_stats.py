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
    'Jahr': 'Year'
}

def log_message(message):
    """Helper function to print timestamps with messages"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Debug function removed as it's no longer needed

def wait_for_table_data(page, timeout=60000):
    """Wait for the table to be populated with data"""
    log_message("Waiting for table data to load...")
    start_time = time.time()
    
    while time.time() - start_time < timeout / 1000:
        try:
            # Check for loading indicators
            loading = page.evaluate("""() => {
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
                    .filter(div => {
                        const text = div.textContent.trim();
                        return text === 'Loading...' || text === 'Lade...' || text === 'Loading' || text === 'Laden';
                    });
                
                return {
                    isLoading: loadingIndicators.length > 0 || loadingDivs.length > 0,
                    hasNoData: document.querySelector('.dataTables_empty') !== null
                };
            }""")
            
            # Check if we have actual data rows
            has_data = page.evaluate("""() => {
                const rows = document.querySelectorAll('#table_1 tbody tr');
                if (rows.length === 0) return false;
                
                // Check if any row has content
                for (const row of rows) {
                    const text = row.textContent.trim();
                    if (text && 
                        !text.includes('No data available') && 
                        !text.includes('Keine Daten verfügbar') &&
                        !text.includes('Loading...') &&
                        !text.includes('Lade...')) {
                        return true;
                    }
                }
                return false;
            }""")
            
            if has_data:
                log_message("Table data loaded successfully")
                return True
                
            # If we have no data but also no loading indicators, we might be done
            if not loading['isLoading'] and not loading['hasNoData'] and page.evaluate("""() => {
                return document.readyState === 'complete';
            }"""):
                log_message("Page fully loaded but no data found")
                return False
                
        except Exception as e:
            log_message(f"Error checking table status: {str(e)}")
        
        time.sleep(1)  # Check every second
    
    log_message("Timed out waiting for table data")
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
    # Read the CSV data
    df = pd.read_csv(StringIO(csv_data))
    
    # Standardize the dataframe (convert German to English, clean data types)
    df = standardize_dataframe(df, is_german=True)
    
    return df

def update_2025_data():
    log_message("Starting weekly update of 2025 data...")
    try:
        with sync_playwright() as p:
            # Launch browser with more options
            log_message("Launching browser...")
            browser = p.chromium.launch(
                headless=True,  # Set to True for production
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
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
            
            # Navigate to page and handle initial setup
            
            # Handle cookie banner
            log_message("Handling cookie banner...")
            handle_cookie_banner(page)
            
            # Wait for the table to be visible
            log_message("Waiting for data table...")
            try:
                page.wait_for_selector("#table_1", timeout=30000)
                log_message("Table found on the page")
            except PlaywrightTimeoutError:
                log_message("Table not found within timeout")
                raise
            
            # Wait for data to load
            if not wait_for_table_data(page, timeout=60000):
                log_message("Failed to load table data")
                raise Exception("Table data did not load")
            
            # Try to set the year filter to 2025...
            log_message("Attempting to set year filter to 2025...")
            
            # First, show the filter row if it's hidden
            try:
                page.evaluate("""() => {
                    const filterRow = document.querySelector('#table_1 thead tr.filters');
                    if (filterRow) filterRow.style.display = '';
                    
                    // Also try to expand any collapsed sections
                    const collapsibles = document.querySelectorAll('[data-toggle="collapse"]');
                    collapsibles.forEach(el => {
                        if (el.getAttribute('aria-expanded') === 'false') {
                            el.click();
                        }
                    });
                }""")
            except Exception as e:
                log_message(f"Error showing filter row: {str(e)}")
            
            # Try to find and set the year filter using multiple approaches
            year_set = False
            
            # Approach 1: Find input with placeholder containing 'jahr' or 'year'
            try:
                year_set = page.evaluate("""() => {
                    try {
                        // Try to find the year filter input
                        const inputs = Array.from(document.querySelectorAll('input'));
                        const yearInput = inputs.find(input => 
                            (input.placeholder && 
                             (input.placeholder.toLowerCase().includes('jahr') || 
                              input.placeholder.toLowerCase().includes('year'))) ||
                            (input.id && 
                             (input.id.toLowerCase().includes('jahr') || 
                              input.id.toLowerCase().includes('year'))) ||
                            (input.name && 
                             (input.name.toLowerCase().includes('jahr') || 
                              input.name.toLowerCase().includes('year')))
                        );
                        
                        if (yearInput) {
                            yearInput.value = '2025';
                            // Trigger change event
                            const event = new Event('input', { bubbles: true });
                            yearInput.dispatchEvent(event);
                            
                            // Also trigger keyup event which is often used by DataTables
                            const keyupEvent = new KeyboardEvent('keyup', { bubbles: true });
                            yearInput.dispatchEvent(keyupEvent);
                            
                            // Also try to trigger the search function directly if available
                            if (window.jQuery && window.jQuery.fn.DataTable) {
                                try {
                                    const table = window.jQuery('#table_1').DataTable();
                                    if (table) {
                                        table.search('2025').draw();
                                    }
                                } catch (e) {
                                    console.error('Error with direct DataTable search:', e);
                                }
                            }
                            
                            return true;
                        }
                        return false;
                    } catch (e) {
                        console.error('Error setting year filter:', e);
                        return false;
                    }
                }""")
                
                if year_set:
                    log_message("Successfully set year filter via input")
                    # Give some time for the filter to apply
                    time.sleep(5)
            except Exception as e:
                log_message(f"Error in year filter approach 1: {str(e)}")
            
            # Approach 2: Try direct DataTable API filtering
            if not year_set:
                log_message("Trying direct DataTable API filtering...")
                try:
                    # Inject jQuery if not present (for DataTables API)
                    page.evaluate("""() => {
                        if (!window.jQuery && !document.querySelector('script[src*="jquery"]')) {
                            const script = document.createElement('script');
                            script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
                            document.head.appendChild(script);
                            return "jQuery injected";
                        }
                        return "jQuery already present";
                    }""")
                    
                    # Wait for jQuery to load
                    time.sleep(2)
                    
                    # Try to use DataTables API to filter
                    filter_result = page.evaluate("""() => {
                        try {
                            if (window.jQuery && window.jQuery.fn.DataTable) {
                                const table = window.jQuery('#table_1').DataTable();
                                if (table) {
                                    // Try different approaches to filter
                                    table.search('2025').draw();
                                    
                                    // Also try column-specific filtering if we can find the year column
                                    const headers = Array.from(document.querySelectorAll('#table_1 thead th'));
                                    for (let i = 0; i < headers.length; i++) {
                                        if (headers[i].textContent.toLowerCase().includes('jahr') || 
                                            headers[i].textContent.toLowerCase().includes('year')) {
                                            table.column(i).search('2025').draw();
                                            return `Filtered column ${i} (${headers[i].textContent}) for 2025`;
                                        }
                                    }
                                    return "Applied general search for 2025";
                                }
                            }
                            return "DataTables not available";
                        } catch (e) {
                            return `Error using DataTables API: ${e.message}`;
                        }
                    }""")
                    
                    log_message(f"DataTable filtering result: {filter_result}")
                    year_set = True
                    time.sleep(5)  # Wait for filtering to apply
                except Exception as e:
                    log_message(f"Error with DataTable API filtering: {str(e)}")
            
            # Approach 3: Find and click the year column header to sort
            if not year_set:
                log_message("Trying column sort approach...")
                try:
                    headers = page.query_selector_all("#table_1 thead th")
                    for i, header in enumerate(headers):
                        header_text = header.inner_text().lower()
                        if "jahr" in header_text or "year" in header_text:
                            # Click twice to sort in descending order (newest first)
                            header.click()
                            time.sleep(1)
                            header.click()
                            log_message(f"Clicked on year column header at index {i} twice to sort newest first")
                            time.sleep(3)  # Wait for sort to complete
                            year_set = True
                            break
                except Exception as e:
                    log_message(f"Error clicking year column: {str(e)}")
            
            # Approach 4: Use the length menu to show all rows
            try:
                page.select_option('select[name="table_1_length"]', value="-1")
                log_message("Set table length to show all rows")
                time.sleep(3)  # Wait for table to update
            except Exception as e:
                log_message(f"Error setting table length: {str(e)}")
            
            # Wait much longer for the table to update after filtering
            log_message("Waiting 60 seconds for table to fully update after filtering...")
            time.sleep(60)  # Significantly increased wait time to ensure data loads
            
            # Proceed with data extraction after filtering
            
            # Extract table data directly from HTML with multiple fallback methods
            log_message("Extracting table data...")
            
            # Method 1: Try DataTables API first
            try:
                log_message("Trying DataTables API extraction...")
                csv_data = page.evaluate("""
                    () => {
                        return new Promise((resolve) => {
                            try {
                                if (window.jQuery && window.jQuery.fn.DataTable) {
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
                                    const csv = headers + '\n' + rows.join('\n');
                                    resolve(csv);
                                } else {
                                    resolve(null);
                                }
                            } catch (e) {
                                console.error('Error extracting via DataTables:', e);
                                resolve(null);
                            }
                        });
                    }
                """)
                
                if csv_data:
                    # Process the downloaded data
                    log_message("Processing data from DataTables API...")
                    df = process_downloaded_data(csv_data)
                    
                    if not df.empty:
                        # Save the processed CSV data
                        log_message("Saving processed data...")
                        df.to_csv("dffl_stats_2025.csv", index=False)
                        log_message(f"Saved updated 2025 data to dffl_stats_2025.csv with {len(df)} rows")
                        log_message(f"Columns: {df.columns.tolist()}")
                        
                        browser.close()
                        log_message("Weekly update completed successfully!")
                        return "dffl_stats_2025.csv"
            except Exception as e:
                log_message(f"Error with DataTables API extraction: {str(e)}")
            
            # Method 2: Try direct DOM extraction with more comprehensive approach
            try:
                log_message("Trying direct DOM extraction...")
                
                # Get all available column headers
                headers = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('#table_1 thead th')).map(th => th.innerText.trim());
                }""")
                
                # Get all data rows
                all_data = []
                page_count = 1
                
                while True:
                    log_message(f"Extracting data from page {page_count}...")
                    
                    # Get current page data
                    page_data = page.evaluate("""(headers) => {
                        const rows = [];
                        const tableRows = document.querySelectorAll('#table_1 tbody tr:not(.dataTables_empty)');
                        
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
                    }""", headers)
                    
                    all_data.extend(page_data)
                    
                    # Try to go to next page
                    next_buttons = page.query_selector_all('.paginate_button.next:not(.disabled)')
                    if not next_buttons or len(next_buttons) == 0:
                        break
                        
                    try:
                        page.click('.paginate_button.next:not(.disabled)')
                        time.sleep(2)  # Wait for page load
                        page_count += 1
                    except:
                        break
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    log_message(f"Extracted {len(df)} total rows via DOM")
                    
                    if not df.empty:
                        # Try to find year column (case insensitive)
                        year_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['jahr', 'year', 'saison', 'season'])]
                        
                        if year_columns:
                            year_col = year_columns[0]
                            log_message(f"Found year column: {year_col}")
                            
                            # Get unique years in the data
                            unique_years = df[year_col].unique()
                            log_message(f"Available years in data: {', '.join(map(str, unique_years))}")
                            
                            # Filter for 2025 data
                            df_2025 = df[df[year_col].astype(str).str.contains('2025')]
                            
                            if not df_2025.empty:
                                # Process the data through the standardization function
                                processed_df = standardize_dataframe(df_2025, is_german=True)
                                
                                # Save the processed data
                                processed_df.to_csv("dffl_stats_2025.csv", index=False)
                                log_message(f"Saved {len(processed_df)} rows of processed 2025 data to dffl_stats_2025.csv")
                                log_message(f"Columns: {processed_df.columns.tolist()}")
                                
                                browser.close()
                                log_message("Weekly update completed successfully!")
                                return "dffl_stats_2025.csv"
                            else:
                                log_message("No 2025 data found in the extracted data")
            except Exception as e:
                log_message(f"Error with DOM extraction: {str(e)}")
                log_message(traceback.format_exc())
            
            # If we get here, both methods failed
            log_message("All data extraction methods failed")
            raise Exception("Failed to extract table data")
            
        # End of with sync_playwright() block
    except Exception as e:
        log_message(f"Error in update_2025_data: {str(e)}")
        log_message(traceback.format_exc())
        raise

if __name__ == "__main__":
    update_2025_data() 