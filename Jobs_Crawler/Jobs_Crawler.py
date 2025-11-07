# Import asyncio for running asynchronous operations.
import asyncio
# Import json for parsing and handling JSON data.
import json
# Import pprint for 'pretty-printing' Python data structures to make them more readable.
import pprint
# Import quote from urllib.parse to safely encode text for use in URLs.
from urllib.parse import quote

# Import the necessary classes from the crawl4ai library for web scraping.
from crawl4ai import (AsyncWebCrawler, BrowserConfig, CacheMode,
                        CrawlerRunConfig, JsonCssExtractionStrategy)
# Import the specific crawler strategy (Playwright) to configure it directly.
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


# Define an asynchronous function, which allows the program to handle long waits (like network requests) efficiently.
async def scrape_jobs():
    """
    Scrapes job listings from Google's career page for a specific query,
    extracts the data using a structured CSS selector schema, and prints the results.
    """
    # 1. DEFINE YOUR SEARCH QUERY
    # This variable holds the job title and location you want to search for.
    job_query = "Data Analyst in kolkata, India"
    # Print a message to the console indicating what is being searched for.
    print(f"Starting job search for: '{job_query}'")

    # 2. CONSTRUCT THE TARGET URL
    # Use the quote function to encode the job_query, replacing spaces and special characters (e.g., ' ' becomes '%20').
    encoded_query = quote(job_query)
    # Create the full URL for the job search results page by appending the encoded query.
    target_url = f"https://www.google.com/about/careers/applications/jobs/results/?q={encoded_query}"

    # 3. DEFINE THE CSS SELECTOR SCHEMA FOR EXTRACTION
    # This dictionary defines a precise map for the crawler to find the exact data points on the webpage.
    # It is more reliable than using natural language prompts for extraction.
    extraction_schema = {
        # A descriptive name for the data being extracted.
        "name": "Google Job Listings",
        # 'baseSelector' is the CSS selector for the parent element that contains each individual job listing.
        # Here, it targets a list item ('li') that has a link ('a') with the class '.WpHeLc' inside it.
        "baseSelector": "li:has(a.WpHeLc)",
        # 'fields' is a list of the specific pieces of data to extract from within each 'baseSelector' element.
        "fields": [
            # Each object defines one piece of data.
            # 'name' is the key for the data in the final JSON output (e.g., "title").
            # 'selector' is the CSS selector to find the element containing the data (e.g., an 'h3' tag with class '.QJPWVe').
            # 'type' specifies what to extract from the selected element (e.g., 'text' gets the visible text).
            {"name": "title", "selector": "h3.QJPWVe", "type": "text"},
            {"name": "location", "selector": "span.r0wTof", "type": "text"},
            # For the URL, the type is 'attribute', which gets the value of a specified HTML attribute ('href' in this case).
            {"name": "url", "selector": "a.WpHeLc", "type": "attribute", "attribute": "href"}
        ]
    }

    # 4. CONFIGURE THE BROWSER
    # Create a configuration object for the underlying web browser.
    browser_config = BrowserConfig(
        # 'headless=True' runs the browser in the background without opening a visible window.
        headless=True,
        # 'user_agent' tells the website what kind of browser is visiting, helping to avoid being blocked.
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    )

    # Print a status message before starting the crawler.
    print(f"Initializing crawler for URL: {target_url}")

    # Use a try...except block to gracefully handle any errors that might occur during the scraping process.
    try:
        # 5. INITIALIZE AND RUN THE CROWLER
        # Create an instance of the specific crawler engine (Playwright) and pass the browser configuration to it.
        playwright_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config)

        # Initialize the main AsyncWebCrawler, telling it to use our pre-configured Playwright strategy.
        # The 'async with' statement ensures the browser is properly started and closed.
        async with AsyncWebCrawler(crawler_strategy=playwright_strategy) as crawler:
            # Configure the settings for this specific crawl job.
            run_config = CrawlerRunConfig(
                # 'cache_mode=CacheMode.BYPASS' tells the crawler to always fetch a fresh version of the page.
                cache_mode=CacheMode.BYPASS,
                # 'extraction_strategy' tells the crawler to use our CSS selector schema to extract data.
                extraction_strategy=JsonCssExtractionStrategy(extraction_schema)
            )

            # Print a status message to indicate that the scraping process is starting.
            print("Crawling in progress... This might take a moment.")
            # Start the crawl by calling the arun() method. 'await' pauses the function until the crawl is complete.
            result = await crawler.arun(url=target_url, config=run_config)
            # Print a confirmation message once the crawl has finished.
            print("Crawling complete!")

            # 6. PROCESS AND DISPLAY THE RESULTS
            # Check if the crawl was successful and if any structured content was extracted.
            if result and result.extracted_content:
                # Print a header for the extracted data.
                print(f"\n--- Extracted Job Listings for '{job_query}' ---")
                # Use a nested try...except block to handle potential errors during JSON parsing.
                try:
                    # Convert the extracted content (which is a JSON string) into a Python list of dictionaries.
                    parsed_data = json.loads(result.extracted_content)

                    # Post-processing: Loop through each job dictionary in the list.
                    for job in parsed_data:
                        # Check if a URL was found and if it's a relative URL (starts with '/').
                        if job.get("url") and job["url"].startswith("/"):
                            # If so, prepend the base domain to make it an absolute, clickable URL.
                            job["url"] = "https://www.google.com" + job["url"]
                    
                    # Use pprint to print the final, cleaned data to the console in a readable format.
                    pprint.pprint(parsed_data)
                    # Open a file named 'extracted_jobs.json' in write mode.
                    with open("extracted_jobs.json", "w") as f:
                        # Save the parsed data to the file, formatted with an indent of 4 spaces for readability.
                        json.dump(parsed_data, f, indent=4)

                # If the extracted content is not valid JSON, this error will be caught.
                except json.JSONDecodeError:
                    # Print an error message and the raw, unparseable content for debugging.
                    print("Could not parse the JSON data. Here is the raw output:")
                    print(result.extracted_content)
                
                # Print a closing line to separate the output.
                print("\n----------------------------------------------------\n")
            # This block runs if the crawl completed but no structured data was extracted.
            else:
                # Print a warning message.
                print("No data was extracted. The website layout might have changed, or no jobs were found.")
                # If a result object exists, print its status code (e.g., 200 for OK).
                if result:
                    print(f"Crawler status: {result.status}")
                    # Print the raw output from the underlying model for debugging purposes.
                    print("\n--- Raw AI Model Output ---")
                    print(result.model_output or "Model output was empty.")
                    print("---------------------------\n")

    # If any exception occurs in the main 'try' block, it will be caught here.
    except Exception as e:
        # Print a generic error message along with the specific exception details.
        print(f"An error occurred during the crawling process: {e}")

# This standard Python construct checks if the script is being run directly.
if __name__ == "__main__":
    # Print a message indicating the start of the script's execution.
    print("Starting a new async event loop.")
    # 'asyncio.run()' starts the asynchronous event loop and runs the main async function ('scrape_jobs') until it's complete.
    asyncio.run(scrape_jobs())