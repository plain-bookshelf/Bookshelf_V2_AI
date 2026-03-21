import pandas as pd
from app.local_test_version.db.session import engine
from sqlmodel import Session, insert
from app.local_test_version.db.schemas import Books

df = pd.read_csv('Bookshelf_sample2.csv')
books = df.iloc[:, :10]
books.columns = ['titles','authors','publisher','school','id_number','call_num','intro','date','img','genres']
records = books.to_dict(orient="records")

with Session(engine) as session:
    session.connection().execute(insert(Books), records)
    session.commit()