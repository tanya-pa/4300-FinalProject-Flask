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

query_sql = "SELECT name, brand, top_notes, middle_notes, base_notes, all_notes, accords, gender, rating, year, url FROM fragrance"
data = mysql_engine.query_selector(query_sql).fetchall()

notes_corpus = [row[5].lower() for row in data] 
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(notes_corpus)

svd = TruncatedSVD(n_components=100)
svd_matrix = svd.fit_transform(tfidf_matrix)

mysql_engine.vectorizer = vectorizer
mysql_engine.svd_matrix = svd_matrix
mysql_engine.svd_model = svd

def sql_search(perfume_query, brand_filter="", gender_filter=""):
    """Search for perfumes based on name, brand, and notes."""
    perfume_query = perfume_query.lower()
    query_vector = mysql_engine.vectorizer.transform([perfume_query])
    query_svd = mysql_engine.svd_model.transform(query_vector)

    results = []
    for i, row in enumerate(data):
        name, brand, top, middle, base, notes, accords, gender, rating, year, url = row

        if brand_filter and brand_filter.lower() not in brand.lower():
            continue
        if gender_filter and gender_filter.lower() not in gender.lower():
            continue

        sim = 1 - cosine(query_svd.ravel(), mysql_engine.svd_matrix[i].ravel())
        sim = 0 if np.isnan(sim) else sim

        normalized_rating = float(rating) / 5.0 if rating else 0
        score = 0.7 * sim + 0.3 * normalized_rating

        results.append((score, row))

    results.sort(key=lambda x: x[0], reverse=True)
    keys = ["name", "brand", "top_notes", "middle_notes", "base_notes", "all_notes", "accords", "gender", "rating", "year", "url"]
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return obj

    return json.dumps(
    [dict(zip(keys, [convert_decimal(val) for val in r[1]])) for r in results[:5]])

@app.route("/")
def home():
    return render_template('base.html', title="Perfume Search")

@app.route("/search")
def perfume_search():
    query = request.args.get("query")
    brand = request.args.get("brand", "")
    gender = request.args.get("gender", "")
    return sql_search(query, brand, gender)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)