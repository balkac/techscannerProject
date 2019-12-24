import os
import sys
import psycopg2 as dbapi2

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is not None:
    config = DATABASE_URL
else:
    config = """dbname='se1' user='postgres' password='1'"""

INIT_STATEMENTS = [

    """CREATE TABLE IF NOT EXISTS USERS (
       ID             SERIAL PRIMARY KEY,
       AD             VARCHAR(100),
       SOYAD          VARCHAR(100),       
       EMAIL          VARCHAR(100) UNIQUE,
       USERNAME       VARCHAR(100) UNIQUE,
       PASSWORD       VARCHAR(100)
   )""",

    """
    CREATE TABLE IF NOT EXISTS WISHLIST (
        WISH_ID        SERIAL PRIMARY KEY,
        USERID         INTEGER REFERENCES USERS (ID)
                       ON UPDATE CASCADE
                       ON DELETE CASCADE,
        URUN_IMAGE     VARCHAR(500),
        URUN_TITLE     VARCHAR(500),
        URUN_LINK      VARCHAR(500),
        URUN_PRICE     VARCHAR(100),
        URUN_LOGO      VARCHAR(100),
        UNIQUE(URUN_LINK, USERID)
    )  """,

]


def initialize(url):
    with dbapi2.connect(url) as connection:
        cursor = connection.cursor()
        for statement in INIT_STATEMENTS:
            cursor.execute(statement)
        cursor.close()

if __name__ == "__main__":
    url = config
    if url is None:
        print("Usage: DATABASE_URL=url python dbinit.py", file=sys.stderr)
        sys.exit(1)
    initialize(url)

   
