from playwright.sync_api import sync_playwright
import pandas as pd
import base64

def fetch_dffl_csv():
    print("Starting fetch_dffl_csv()...")
    try:
        print("Starting Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            print("Navigating to DFFL site...")
            page.goto("https://www.5erdffl.de/player-stats/", timeout=90000)
            
            print("Setting filter to 'All' (17,000 rows)...")
            page.select_option('select[name="table_1_length"]', value="-1")
            
            print("Waiting for table to update (up to 60 seconds)...")
            page.wait_for_timeout(60000)
            
            print("Checking if table has loaded...")
            page.wait_for_selector("table#table_1 tbody tr", timeout=90000)
            
            # Log console messages for debugging
            def handle_console(msg):
                print(f"Console message: {msg.text}")
            page.on("console", handle_console)
            
            # Approach 1: Extract table data using DataTables API
            print("Waiting for DataTables to initialize...")
            page.wait_for_function("typeof window.jQuery !== 'undefined' && typeof window.jQuery.fn.dataTable !== 'undefined'", timeout=60000)
            
            print("Extracting table data using DataTables API...")
            csv_data = page.evaluate("""
                (function() {
                    try {
                        const table = document.querySelector('#table_1');
                        if (table && typeof window.jQuery !== 'undefined' && typeof window.jQuery.fn.dataTable !== 'undefined') {
                            const dt = window.jQuery(table).DataTable();
                            // Get all table data (including headers)
                            const data = dt.rows().data().toArray();
                            const headers = dt.columns().header().toArray().map(header => header.innerText);
                            // Format as CSV
                            let csv = headers.join(',') + '\\n';
                            data.forEach(row => {
                                const rowData = row.map(cell => `"${cell.toString().replace(/"/g, '""')}"`).join(',');
                                csv += rowData + '\\n';
                            });
                            return csv;
                        }
                        return null;
                    } catch (e) {
                        console.log('Error in DataTables extraction:', e.message);
                        return null;
                    }
                })();
            """)
            
            if csv_data:
                print("Saving CSV data directly...")
                with open("dffl_stats.csv", "w", encoding="utf-8") as f:
                    f.write(csv_data)
                print("CSV saved successfully!")
            else:
                # Approach 2: Fall back to capturing the Blob URL
                print("DataTables extraction failed, falling back to Blob capture...")
                print("Injecting script to capture Blob URLs...")
                page.evaluate("""
                    (function() {
                        const originalCreateObjectURL = window.URL.createObjectURL;
                        window.URL.createObjectURL = function(blob) {
                            const url = originalCreateObjectURL.call(window.URL, blob);
                            console.log('Captured Blob URL:', url);
                            window.capturedBlobUrl = url;
                            // Fetch the Blob and convert to base64
                            fetch(url)
                                .then(res => res.blob())
                                .then(blob => {
                                    const reader = new FileReader();
                                    reader.onloadend = () => {
                                        window.capturedBlobData = reader.result;
                                    };
                                    reader.readAsDataURL(blob);
                                });
                            return url;
                        };
                    })();
                """)
                
                print("Waiting for CSV export button to be visible...")
                page.wait_for_selector('a.dt-button.buttons-csv.buttons-html5[aria-controls="table_1"]', state="visible", timeout=60000)
                print("Ensuring CSV export button is not disabled...")
                button = page.locator('a.dt-button.buttons-csv.buttons-html5[aria-controls="table_1"]')
                if button.is_disabled():
                    raise Exception("CSV export button is disabled")
                if not button.is_visible():
                    raise Exception("CSV export button is not visible")
                
                print("Simulating a full click sequence on CSV export button...")
                button.dispatch_event("mousedown")
                button.dispatch_event("mouseup")
                button.dispatch_event("click")
                print("Clicking CSV export button with JavaScript as fallback...")
                page.evaluate('document.querySelector("a.dt-button.buttons-csv.buttons-html5[aria-controls=\'table_1\']").click()')
                
                print("Waiting for Blob URL to be captured (up to 60 seconds)...")
                page.wait_for_timeout(60000)
                blob_url = page.evaluate("window.capturedBlobUrl")
                blob_data = page.evaluate("window.capturedBlobData")
                if blob_data:
                    # Extract base64 data (remove "data:text/csv;base64," prefix)
                    base64_data = blob_data.split(",")[1]
                    with open("dffl_stats.csv", "wb") as f:
                        f.write(base64.b64decode(base64_data))
                    print("CSV downloaded successfully from Blob!")
                else:
                    raise Exception("Failed to capture Blob URL or data")
            
            print("Closing browser...")
            browser.close()
            print("Fetch completed successfully!")
            return "dffl_stats.csv"
    except Exception as e:
        print(f"Error in fetch_dffl_csv(): {str(e)}")
        raise

if __name__ == "__main__":
    fetch_dffl_csv()