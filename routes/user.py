import os
import base64
import uuid
import logging
from flask import request, jsonify, render_template, send_from_directory
import mysql.connector
from app import app
from PIL import Image
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='flutter'
    )


app.config['CROPPED_FOLDER'] = 'static/images/cropped'
app.config['COMPRESSED_FOLDER'] = 'static/images/compressed'


@app.route('/admin/user')
def user():
    return render_template("admin/user.html")


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        data = request.form
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')
        password = data.get('password')



        image_data = request.files.get('image') or data.get('image')
        original_image = request.files.get('original') or data.get('original')

        image_name = None
        original_name = None

        def compress_image(image_file, save_path):
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()

            print(f"File size: {file_size / 1024 / 1024} MB")
            if file_size > 2 * 1024 * 1024:
                image_file.seek(0)
                img = Image.open(image_file)
                img = img.convert("RGB")
                img.save(save_path, format='JPEG', quality=75)
                return True
            else:
                image_file.seek(0)
                image_file.save(save_path)
                return False

        if image_data:
            if isinstance(image_data, str):
                image_path = save_base64_image(image_data, app.config['CROPPED_FOLDER'])
                image_name = os.path.basename(image_path)
            else:
                filename = secure_filename(image_data.filename)
                image_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
                image_data.save(image_path)
                image_name = filename

                compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
                compress_image(image_data, compressed_path)

        if original_image:
            if isinstance(original_image, str):
                original_path = save_base64_image(original_image, app.config['COMPRESSED_FOLDER'])
                original_name = os.path.basename(original_path)
            else:
                filename = secure_filename(original_image.filename)
                original_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
                original_image.save(original_path)
                original_name = filename

                compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
                compress_image(original_image, compressed_path)

        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO user (name, gender, phone, email, image, password) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, gender, phone, email, image_name or original_name, password))
        connection.commit()

        cursor.close()
        connection.close()


        return jsonify({'message': 'User added successfully'}), 201

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        cursor.close()
        connection.close()
        return jsonify(users), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/delete_user/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT image FROM user WHERE id = %s", (id,))
        user = cursor.fetchone()

        if user and user[0]:
            cropped_image_path = os.path.join('static', 'images', 'cropped', user[0])
            compressed_image_path = os.path.join('static', 'images', 'compressed', user[0])

            if os.path.exists(cropped_image_path):
                os.remove(cropped_image_path)

            if os.path.exists(compressed_image_path):
                os.remove(compressed_image_path)

        query = "DELETE FROM user WHERE id = %s"
        cursor.execute(query, (id,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/update_user/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        data = request.form
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')
        password = data.get('password')

        image_data = request.files.get('image') or data.get('image')
        image_path = None

        original_image = request.files.get('original') or data.get('original')
        original_path = None

        def compress_image(image_file, save_path):
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            if file_size > 2 * 1024 * 1024:
                image_file.seek(0)
                img = Image.open(image_file)
                img = img.convert("RGB")
                img.save(save_path, format='JPEG', quality=75)
                return True
            else:
                image_file.seek(0)
                image_file.save(save_path)
                return False

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE id = %s", (id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if image_data:
            if isinstance(image_data, str):
                image_path = save_base64_image(image_data, app.config['CROPPED_FOLDER'])
                image_name = os.path.basename(image_path)
            else:
                filename = secure_filename(image_data.filename)
                image_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
                image_data.save(image_path)
                image_name = filename

                compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
                compress_image(image_data, compressed_path)

            if user.get('image'):
                old_image_cropped = os.path.join(app.config['CROPPED_FOLDER'], user['image'])
                old_image_compressed = os.path.join(app.config['COMPRESSED_FOLDER'], user['image'])
                if os.path.exists(old_image_cropped):
                    os.remove(old_image_cropped)
                if os.path.exists(old_image_compressed):
                    os.remove(old_image_compressed)

        if original_image:
            filename = secure_filename(original_image.filename)
            original_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
            original_image.save(original_path)

        query = """
        UPDATE user 
        SET name = %s, gender = %s, phone = %s, email = %s, image = %s, password = %s 
        WHERE id = %s
        """
        cursor.execute(query, (
            name or user['name'],
            gender or user['gender'],
            phone or user['phone'],
            email or user['email'],
            image_name if image_data else user['image'],
            password or user['password'],
            id
        ))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


def save_base64_image(base64_str, cropped_folder):
    try:
        if not os.path.exists(cropped_folder):
            os.makedirs(cropped_folder)

        compressed_folder = 'static/images/compressed/'
        if not os.path.exists(compressed_folder):
            os.makedirs(compressed_folder)

        image_data = base64.b64decode(base64_str.split(",")[1])
        file_name = f"{uuid.uuid4().hex}.jpg"

        cropped_path = os.path.join(cropped_folder, file_name)
        with open(cropped_path, "wb") as f:
            f.write(image_data)

        return file_name
    except Exception as e:
        logging.error(f"Error saving Base64 image: {e}")
        raise


def save_uploaded_file(uploaded_file, cropped_folder):
    try:
        if not os.path.exists(cropped_folder):
            os.makedirs(cropped_folder)

        compressed_folder = 'static/images/compressed/'
        if not os.path.exists(compressed_folder):
            os.makedirs(compressed_folder)

        file_name = f"{uuid.uuid4().hex}.jpg"

        cropped_path = os.path.join(cropped_folder, file_name)
        uploaded_file.save(cropped_path)

        compressed_path = os.path.join(compressed_folder, file_name)
        uploaded_file.save(compressed_path)

        return file_name
    except Exception as e:
        logging.error(f"Error saving uploaded file: {e}")
        raise


@app.route('/static/images/cropped/<filename>')
def serve_image(filename):
    return send_from_directory('static/images/cropped', filename)


@app.route('/static/images/compressed/<filename>')
def serve_compressed_image(filename):
    return send_from_directory(app.config['COMPRESSED_FOLDER'], filename)


if __name__ == "__main__":
    app.run(debug=True)
