from app import app, render_template
from flask import request, jsonify
import mysql.connector


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='flutter'
    )
    return connection



@app.route('/admin/category')
def category():
    return render_template("admin/category.html")



@app.route('/add_category', methods=['POST'])
def add_category():
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')

        connection = get_db_connection()
        cursor = connection.cursor()

        query = "INSERT INTO category (name, description) VALUES (%s, %s)"
        cursor.execute(query, (name, description))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Category added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM category")
        categories = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify(categories), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_category/<int:id>', methods=['PUT'])
def update_category(id):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')

        connection = get_db_connection()
        cursor = connection.cursor()

        query = "UPDATE category SET name = %s, description = %s WHERE id = %s"
        cursor.execute(query, (name, description, id))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Category updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_category/<int:id>', methods=['DELETE'])
def delete_category(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = "DELETE FROM category WHERE id = %s"
        cursor.execute(query, (id,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Category deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
