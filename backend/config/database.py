import psycopg2

def get_connection():
    return psycopg2.connect(
        host="postgres.railway.internal",
        dbname="railway",
        user="postgres",
        password="dhuudOCvDKVgQokLiWCWtpYIMDFMiAql",
        port=5432
    )

