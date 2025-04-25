import pandas as pd
import re
import ast
import html
import json

df = pd.read_csv("reduced_dataset.csv")
df['size_estimate'] = df.apply(lambda row: sum(len(str(row[col])) for col in ['Perfume', 'Brand', 'Top', 'Middle', 'Base', 'Notes', 'Accords', 'Gender', 'url', 'reviews', 'description', 'matching_image_urls']), axis=1)
df = df.sort_values('size_estimate').head(8500)

def clean_reviews(reviews):
    try:
        reviews = ast.literal_eval(html.unescape(reviews))
    except (SyntaxError, ValueError):
        return []
    if not isinstance(reviews, list):
        return []
    cleaned_reviews = []
    for review in reviews:
        if not isinstance(review, str):
            continue
        review = re.sub(r'[\U00010000-\U0010ffff]', '', review)  # remove emojis
        review = re.sub(r'[^\x00-\x7F]+', ' ', review)  # remove non-ASCII
        review = re.sub(r'[%©®™•·✓→←]', '', review)  # remove specific symbols
        review = re.sub(r'\s+', ' ', review)  # remove excess whitespace
        review = review.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
        review = review.strip()
        cleaned_reviews.append(review)
    return cleaned_reviews

with open("init.sql", "w", encoding="utf-8") as f:
    f.write("DROP TABLE IF EXISTS fragrance;\n")
    f.write("""
    CREATE TABLE fragrance (
    name VARCHAR(255),
    brand VARCHAR(255),
    top_notes TEXT,
    middle_notes TEXT,
    base_notes TEXT,
    all_notes TEXT,
    accords TEXT,
    gender VARCHAR(255),
    url TEXT,
    rating DECIMAL(3, 2),
    year VARCHAR(10),
    country VARCHAR(255),
    reviews LONGTEXT,
    description TEXT,
    image TEXT
);\n\n""")

    for _, row in df.iterrows():
        def clean(s):
            s = str(s).replace("'", "''") 
            s  = s.replace('%', '%%')
            return s

        name = clean(row['Perfume'])
        brand = clean(row['Brand'])
        top = clean(row['Top'])
        middle = clean(row['Middle'])
        base = clean(row['Base'])
        all_notes = clean(row['Notes'])
        accords = clean(row['Accords'])
        gender = clean(row['Gender'])
        url = clean(row['url'])
        rating = clean(row['Rating Value'])
        year_val = row['Year']
        year = "'N/A'" if year_val == 0 else f"'{int(year_val)}'"
        country = clean(row['Country'])
        safe_reviews = clean_reviews(row['reviews'])
        reviews = clean(json.dumps(safe_reviews))  
        description = clean(row['description'])
        image = clean(row['matching_image_urls'])

        f.write(
            f"INSERT INTO fragrance (name, brand, top_notes, middle_notes, base_notes, all_notes, accords, gender, url, rating, year, country, reviews, description, image)"
            f"VALUES ('{name}', '{brand}',  '{top}', '{middle}', '{base}', '{all_notes}', '{accords}', '{gender}', '{url}', {rating}, {year}, '{country}', '{reviews}', '{description}', '{image}');\n"
        )
