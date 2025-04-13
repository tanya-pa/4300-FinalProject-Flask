# script to scrape from fragrantica website
# attributes needed: 
# - accords
# - notes (top, bottom, medium) -> merge all in preprocessing
# - occasion: winter, spring, fall, summer, day/night time (presumably integers)
# - brand (that they already like)
# - gender  (man, woman, unisex) 
# - rating
# - number of votes
# - listed prices (if available)
# - longevity (if available)
import requests
from bs4 import BeautifulSoup

def scrape_fragrance_details(fragrance_url):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' 
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/105.0.0.0 Safari/537.36')
    }
    
    try:
        response = requests.get(fragrance_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error accessing URL: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extracting Accords
    accords = []
    accords_section = soup.find("div", class_="accords")
    if accords_section:
        accords = [item.get_text(strip=True) for item in accords_section.find_all("span", class_="accord-name")]
        
    # Extracting Notes: Top, Middle, and Base --
    notes = {"top": [], "middle": [], "base": []}
    top_section = soup.find("div", id="top-notes")
    if top_section:
        notes["top"] = [item.get_text(strip=True) for item in top_section.find_all("a", class_="note")]
    
    middle_section = soup.find("div", id="middle-notes")
    if middle_section:
        notes["middle"] = [item.get_text(strip=True) for item in middle_section.find_all("a", class_="note")]
    
    base_section = soup.find("div", id="base-notes")
    if base_section:
        notes["base"] = [item.get_text(strip=True) for item in base_section.find_all("a", class_="note")]
    
    # Extracting Occasion
    occasion = []
    occasion_section = soup.find("div", class_="occasions")
    if occasion_section:
        occasion = [item.get_text(strip=True) for item in occasion_section.find_all("span", class_="occasion-item")]
    
    
    # Extracting Gender
    gender = ""
    gender_tag = soup.find("span", class_="gender")
    if gender_tag:
        gender = gender_tag.get_text(strip=True)
    
    # Extracting Rating 
    rating = None
    rating_tag = soup.find("span", class_="rating-value")
    if rating_tag:
        try:
            rating = float(rating_tag.get_text(strip=True))
        except ValueError:
            rating = None
    
    # Extracting Number of Votes
    votes = None
    votes_tag = soup.find("span", class_="rating-count")
    if votes_tag:
        try:
            votes = int(votes_tag.get_text(strip=True).split()[0])
        except (ValueError, IndexError):
            votes = None
    
    # Extracting Listed Prices
    prices = []
    price_section = soup.find("div", class_="prices")
    if price_section:
        prices = [item.get_text(strip=True) for item in price_section.find_all("span", class_="price")]

    
    # dictionary
    details = {
        "accords": accords,
        "notes": notes,  
        "occasion": occasion,
        "gender": gender,
        "rating": rating,
        "votes": votes,
        "prices": prices,
    }
    
    return details

#
if __name__ == "__main__":
    # Replace with an actual Fragrantica URL of a perfume page
    test_url = ""
    additional_data = scrape_fragrance_details(test_url)
    if additional_data:
        print("Scraped Data:")
        print(additional_data)

