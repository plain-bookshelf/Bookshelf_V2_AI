import pandas as pd

df_excel = pd.read_excel("school_books.xlsx", dtype=str).fillna("")