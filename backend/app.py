import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from decimal import Decimal
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from scipy.spatial.distance import cosine
import numpy as np

# ROOT_PATH for linking with all your files. 
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..",os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
LOCAL_MYSQL_USER = "root"
LOCAL_MYSQL_USER_PASSWORD = "eaudeyou4300"
LOCAL_MYSQL_PORT = 3306
LOCAL_MYSQL_DATABASE = "kardashiandb"

mysql_engine = MySQLDatabaseHandler(LOCAL_MYSQL_USER,LOCAL_MYSQL_USER_PASSWORD,LOCAL_MYSQL_PORT,LOCAL_MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

query_sql = "SELECT name, brand, top_notes, middle_notes, base_notes, all_notes, accords, gender, rating, year, country, url, reviews, description, image FROM fragrance"
data = mysql_engine.query_selector(query_sql).fetchall()

def extract_reviews(reviews_raw):
    try:
        reviews = json.loads(reviews_raw)
        if isinstance(reviews, list):
            return " ".join(reviews).lower()
        return str(reviews).lower()
    except Exception:
        return ""

notes_corpus = [f"{row[5].lower()} {row[6].lower()} {row[0].lower()} {extract_reviews(row[12])} {{row[13].lower()}}" for row in data]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(notes_corpus)

country_mappings = {
    "u.k.": "uk",
    "united kingdom": "uk",
    "united states": "usa",
    "us": "usa",
    "u.s.": "usa",
    "u.s.a.": "usa",
    "united states of america": "usa",
    "u.a.e.": "uae",
    "united arab emirates": "uae",
    "saudi arabia":"arabia saudi"
}

svd = TruncatedSVD(n_components=100)
svd_matrix = svd.fit_transform(tfidf_matrix)

# Identify the top 8 most important latent dimensions by explained variance
explained_variance = svd.explained_variance_ratio_
top_k = 8
top_dimensions_indices = np.argsort(explained_variance)[::-1][:top_k]

# Store in a global variable
latent_indices = top_dimensions_indices.tolist()

mysql_engine.vectorizer = vectorizer
mysql_engine.svd_matrix = svd_matrix
mysql_engine.svd_model = svd

def sql_search(perfume_query, brand_filter="", gender_filter="", country_filter=""):
    """Search for perfumes based on name, brand, country, gender, and notes."""
    perfume_query = perfume_query.lower()
    country_filter = country_filter.strip().lower()
    country_filter = country_mappings.get(country_filter, country_filter)
    query_vector = mysql_engine.vectorizer.transform([perfume_query])
    query_svd = mysql_engine.svd_model.transform(query_vector)

    results = []
    for i, row in enumerate(data):
        name, brand, top, middle, base, notes, accords, gender, rating, year, country, url, reviews_og, description, image = row
        if brand_filter and brand_filter.lower() not in brand.lower():
            continue
        if gender_filter and gender_filter.lower() != gender.lower():
            continue
        if country_filter and country_filter.strip().lower() not in country.strip().lower():
            continue
        if perfume_query.strip() == "":
            sim = 1.0
        else:
            sim = abs(1 - cosine(query_svd.ravel(), mysql_engine.svd_matrix[i].ravel()))
            sim = 0.0 if np.isnan(sim) else sim

        # get best review
        try:
            reviews = json.loads(reviews_og)
            if isinstance(reviews, list) and reviews:
                review_vectors = mysql_engine.vectorizer.transform(reviews)
                review_similarities = [1 - cosine(query_vector.toarray(), rv.toarray()) for rv in review_vectors]
                best_review_index = int(np.argmax(review_similarities))
                best_review = reviews[best_review_index]
            else:
                best_review = ""
        except Exception:
            best_review = ""

        normalized_rating = float(rating) / 5.0 if rating else 0
        score = 0.7 * sim + 0.3 * normalized_rating
        sim = sim*100
        results.append((score, sim, row, best_review))

    results.sort(key=lambda x: x[0], reverse=True)
    keys = ["name", "brand", "top_notes", "middle_notes", "base_notes", "all_notes", "accords", "gender", "rating", "year", "country", "url", "image"]
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    top_results = []
    for score, sim, row, best_review in results[:5]:
        perfume = dict(zip(keys, [convert_decimal(val) for val in row]))
        perfume['name'] = perfume['name'].title()
        perfume['brand'] = perfume['brand'].title()
        perfume['display_name'] = f"{perfume['name']} by {perfume['brand']}"
        perfume['rating_value'] = f"{perfume['rating']}"
        perfume['similarity_score'] = f"{sim:.2f}"
        perfume['best_review'] = best_review
        perfume["image"] = image
        
        # Get SVD feature names
        svd_vector = mysql_engine.svd_matrix[data.index(row)]
        feature_names = vectorizer.get_feature_names_out()
        components = svd.components_

        # Extract the top term for each latent dimension
        top_terms = {}
        for dim in latent_indices:
            top_idx = components[dim].argmax()
            top_term = feature_names[top_idx]
            top_terms[dim] = top_term

        # Normalize latent profile values
        latent_scores = [svd_vector[dim] for dim in latent_indices]
        min_val = min(latent_scores)
        max_val = max(latent_scores)
        range_val = max_val - min_val if max_val != min_val else 1  # avoid divide-by-zero

        normalized_profile = {
            top_terms[dim]: round((svd_vector[dim] - min_val) / range_val, 4) for dim in latent_indices
        }

        perfume['latent_profile'] = normalized_profile
        
        top_results.append(perfume)

    if not top_results:
        return json.dumps([])
    
    return json.dumps(top_results, default=convert_decimal)
    
    

@app.route("/")
def home():
    return render_template('base.html', title="Perfume Search")

@app.route("/search")
def perfume_search():
    query = request.args.get("query")
    brand = request.args.get("brand", "")
    gender = request.args.get("gender", "")
    country = request.args.get("country", "")
    return sql_search(query, brand, gender, country)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)