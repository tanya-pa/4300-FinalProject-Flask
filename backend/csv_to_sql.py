import pandas as pd

df = pd.read_csv("frag_clean.csv")  #i put the frag_clean under back end folder for now 

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
    accords TEXT
);\n\n""")

    for _, row in df.iterrows():
        def clean(s):
            return str(s).replace("'", "''") if pd.notnull(s) else ""

        name = clean(row['Perfume'])
        brand = clean(row['Brand'])
        top = clean(row['Top'])
        middle = clean(row['Middle'])
        base = clean(row['Base'])
        all_notes = clean(row['Notes'])
        accords = clean(row['Accords'])

        f.write(
            f"INSERT INTO fragrance (name, brand, top_notes, middle_notes, base_notes, all_notes, accords) "
            f"VALUES ('{name}', '{brand}',  '{top}', '{middle}', '{base}', '{all_notes}', '{accords}');\n"
        )
