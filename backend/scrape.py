import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

def scrape_season_bars_and_image(url):
    # Setup browser with user-agent and SSL error handling
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "voting-small-chart-size"))
        )

        time.sleep(random.uniform(2, 4))  # small delay

        # Scrape season votes
        labels = ['winter', 'spring', 'summer', 'fall', 'day', 'night']
        season_votes = {}

        bars = driver.find_elements(By.XPATH, "//div[@class='voting-small-chart-size']//div/div")

        for label, bar in zip(labels, bars):
            style = bar.get_attribute("style")
            width = 0.0
            if style and "width" in style:
                try:
                    width_str = style.split("width:")[1].split("%")[0].strip()
                    width = float(width_str)
                except:
                    pass
            season_votes[label] = width

        # Scrape perfume image URL
        image_url = None
        try:
            image_element = driver.find_element(By.XPATH, "//div[@class='cell small-12']//img[@itemprop='image']")
            image_url = image_element.get_attribute("src")
        except Exception as e:
            print(f"Error extracting image URL for {url}: {e}")
        
        #Scrape Longevity 
        longevity_data = []
        try:
            # Locate all longevity rows
            longevity_rows = driver.find_elements(By.XPATH, "//div[@class='grid-x grid-margin-x']")
            for row in longevity_rows:
                try:
                    # Extract the vote button name and legend
                    name_element = row.find_element(By.CLASS_NAME, "vote-button-name")
                    legend_element = row.find_element(By.CLASS_NAME, "vote-button-legend")
                    name = name_element.text.strip()
                    legend = legend_element.text.strip()
                    longevity_data.append({"category": name, "value": legend})
                except Exception as e:
                    print(f"Error extracting a longevity row: {e}")
        except Exception as e:
            print(f"Error extracting longevity data for {url}: {e}")
        
        #Scrape User Reviews (Positive, Negative)
# Scrape User Reviews (Positive, Negative)
        # Scrape Price Range
        price_range = ""
        try:
            price_div = driver.find_element(By.XPATH, "//div[contains(text(), 'Online shops offers') or contains(., 'FragranceNet')]")
            price_text = price_div.text.strip()
            print(f"Price info text: {price_text}")

            import re
            match = re.search(r"(\d+\.\d{2})\s*-\s*(\d+\.\d{2})", price_text)
            if match:
                price_range = f"{match.group(1)} - {match.group(2)} USD"
            else:
                print("No price range found.")
        except Exception as e:
            print(f"Error extracting price range: {e}")


        return {"season_votes": season_votes, "image_url": image_url, "longevity_data": longevity_data}

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {
            "season_votes": {label: 0.0 for label in ['winter', 'spring', 'summer', 'fall', 'day', 'night']},
            "image_url": None,
            "longevity_data": [], 
        }
    finally:
        driver.quit()

def process_urls(input_csv, output_csv):
    # Load the CSV file
    df = pd.read_csv(input_csv)

    # Ensure the dataset has a 'url' column
    if 'url' not in df.columns:
        print("Error: The input CSV must contain a 'url' column.")
        return

    # Add new columns for season votes and image URL
    df['season_votes'] = None
    df['image_url'] = None
    df['longevity_data'] = None

    # Process each URL
    for index, row in df.iterrows():
        url = row['url']
        print(f"Processing URL {index + 1}/{len(df)}: {url}")
        result = scrape_season_bars_and_image(url)
        df.at[index, 'season_votes'] = str(result["season_votes"])  # Store as a string to fit in a single column
        df.at[index, 'image_url'] = result["image_url"]
        df.at[index, 'longevity_data'] = str(result["longevity_data"])

    # Save the updated dataset to a new CSV file
    df.to_csv(output_csv, index=False)
    print(f"Updated dataset saved to {output_csv}")

# Test the scraper with the CSV file
if __name__ == "__main__":
    input_csv = "frag_clean2.csv"  # Input CSV file
    output_csv = "frag_cleaned2_with_season_votes_and_images.csv"  # Output CSV file
    process_urls(input_csv, output_csv)