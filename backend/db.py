import mysql.connector
from config import DB_CONFIG


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("MySQL connected!")
        return connection

    except mysql.connector.Error as error:
        print("Database connection error:", error)
        return None