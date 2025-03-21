import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine
from rapidfuzz.distance import Levenshtein
from collections import Counter
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

def wagner_fischer(s1, s2):
    """Compute the edit distance between two strings using the Wagner-Fischer algorithm."""
    len_s1, len_s2 = len(s1), len(s2)
    dp = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    for i in range(len_s1 + 1):
        for j in range(len_s2 + 1):
            if i == 0:
                dp[i][j] = j  
            elif j == 0:
                dp[i][j] = i  
            elif s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], 
                                   dp[i][j - 1],   
                                   dp[i - 1][j - 1]) 

    return dp[len_s1][len_s2]

def sql_search(perfume_query):
    """Search for perfumes based on name, brand, and notes."""
    perfume_query = perfume_query.lower()

    query_sql = "SELECT name, brand, all_notes, accords FROM fragrance"
    data = mysql_engine.query_selector(query_sql).fetchall()

    perfumes = []
    notes_corpus = [row[2].lower() for row in data] 

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(notes_corpus)  
    query_vector = vectorizer.transform([perfume_query])  

    for i, row in enumerate(data):
        perfume_name = row[0].lower()  
        brand_name = row[1].lower()  
        all_notes = row[2].lower()  
        accords = row[3].lower()  

        name_distance = wagner_fischer(perfume_query, perfume_name)
        brand_distance = wagner_fischer(perfume_query, brand_name)

        notes_similarity = 1 - cosine(tfidf_matrix[i].toarray().ravel(), query_vector.toarray().ravel())  
        if np.isnan(notes_similarity):  
            notes_similarity = 0  

        normalized_name_score = 1 / (1 + name_distance)
        normalized_brand_score = 1 / (1 + brand_distance)

        final_score = (0.5 * normalized_name_score) + (0.3 * normalized_brand_score) + (0.7 * notes_similarity)
        perfumes.append((final_score, row))

    perfumes.sort(key=lambda x: x[0], reverse=True)
    keys = ["name", "brand", "all_notes", "accords"]
    top_matches = [dict(zip(keys, perfume[1])) for perfume in perfumes[:5]]

    return json.dumps(top_matches)

@app.route("/")
def home():
    return render_template('base.html', title="Perfume Search")

@app.route("/search")
def perfume_search():
    query = request.args.get("query")
    return sql_search(query)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)