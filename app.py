from flask import Flask, render_template
import mysql.connector


app = Flask(__name__)


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='flutter'
    )
    return connection


connection = get_db_connection()
cursor = connection.cursor()

import routes


if __name__ == '__main__':
    app.run()
