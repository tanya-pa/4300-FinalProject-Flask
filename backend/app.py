import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler

# ROOT_PATH for linking with all your files. 
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..",os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
LOCAL_MYSQL_USER = "root"
LOCAL_MYSQL_USER_PASSWORD = "eaudeyou4300"
LOCAL_MYSQL_PORT = 3306
LOCAL_MYSQL_DATABASE = "frag_proto"

mysql_engine = MySQLDatabaseHandler(LOCAL_MYSQL_USER,LOCAL_MYSQL_USER_PASSWORD,LOCAL_MYSQL_PORT,LOCAL_MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db(os.path.join(os.environ['ROOT_PATH'],'init_new.sql'))

app = Flask(__name__)
CORS(app)

def sql_search(perfume):
    query_sql = f"""
        SELECT * FROM fragrance 
        WHERE LOWER(name) LIKE '%%{perfume.lower()}%%' 
        OR LOWER(brand) LIKE '%%{perfume.lower()}%%' 
        OR LOWER(all_notes) LIKE '%%{perfume.lower()}%%' 
        OR LOWER(accords) LIKE '%%{perfume.lower()}%%' 
        LIMIT 5
    """
    keys = ["name", "brand", "top_notes", "middle_notes", "base_notes", "all_notes", "accords"]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/search")
def perfume_search():
    query = request.args.get("query")
    return sql_search(query)

# Sample search, the LIKE operator in this case is hard-coded, 
# but if you decide to use SQLAlchemy ORM framework, 
# there's a much better and cleaner way to do this
# def sql_search(episode):
#     query_sql = f"""SELECT * FROM episodes WHERE LOWER( title ) LIKE '%%{episode.lower()}%%' limit 10"""
#     keys = ["id","title","descr"]
#     data = mysql_engine.query_selector(query_sql)
#     return json.dumps([dict(zip(keys,i)) for i in data])

# @app.route("/")
# def home():
#     return render_template('base.html',title="sample html")

# @app.route("/episodes")
# def episodes_search():
#     text = request.args.get("title")
#     return sql_search(text)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)