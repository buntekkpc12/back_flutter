from flask import request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import bcrypt
from app import app
import jwt
import datetime
import os
from werkzeug.utils import secure_filename

CORS(app)

flutter_folder = os.path.join('C:\\Users\\Admin\\StudioProjects\\final_project', 'assets', 'profile')
app.config['UPLOAD_FOLDER'] = flutter_folder

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='flutter'
    )


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/admin/auth')
def auth():
    return render_template("admin/auth.html")


@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        username = data['username']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM auth_flutter WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"success": False, "message": "Email already registered"})

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute(
            "INSERT INTO auth_flutter (username, email, password, is_login) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, False)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Registration successful"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json

        if not data.get('email') or not data.get('password'):
            return jsonify({"success": False, "message": "Email and password are required"}), 400

        email = data['email']
        password = data['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM auth_flutter WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                is_login = user['is_login']

                cursor.execute(
                    "UPDATE auth_flutter SET is_login = TRUE WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()

                return jsonify({
                    "success": True,
                    "message": "Login successful",
                    "is_login": bool(is_login),
                })
            else:
                return jsonify({"success": False, "message": "Invalid email or password"}), 400
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/add_address', methods=['POST'])
def add_address():
    try:
        data = request.json

        required_fields = ['user_id', 'name', 'addressline1', 'addressline2', 'city', 'postalcode', 'country']
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "All fields are required"}), 400

        user_id = data['user_id']
        name = data['name']
        addressline1 = data['addressline1']
        addressline2 = data['addressline2']
        city = data['city']
        postalcode = data['postalcode']
        country = data['country']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO address (user_id, name, addressline1, addressline2, city, postalcode, country)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, name, addressline1, addressline2, city, postalcode, country))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Address added successfully"
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/get_address', methods=['GET'])
def get_address():
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({"success": False, "message": "User ID is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT name, addressline1, addressline2, city, postalcode, country
            FROM address WHERE user_id = %s
        """, (user_id,))
        addresses = cursor.fetchall()

        if not addresses:
            return jsonify({
                "success": False,
                "message": "No addresses found for the given user ID"
            }), 404

        for address in addresses:
            address['full_address'] = f"{address['addressline1']}, {address['addressline2']}, {address['city']}, {address['postalcode']}, {address['country']}"

        return jsonify({
            "success": True,
            "addresses": addresses
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/logout', methods=['POST'])
def logout():
    try:
        email = request.json.get('email')

        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE auth_flutter SET is_login = %s WHERE email = %s", (False, email))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Email not found"}), 404

        return jsonify({"success": True, "message": "Logout successful"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/get_logged_in_user', methods=['GET'])
def get_logged_in_user():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, username, email, image FROM auth_flutter WHERE is_login = TRUE LIMIT 1")
        user = cursor.fetchone()

        if user:
            print(f"Logged-in user found: {user}")
            return jsonify(user), 200
        else:
            print("No logged-in user found.")
            return jsonify({"error": "No user is currently logged in"}), 404
    except Exception as e:
        print(f"Error fetching logged-in user: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        user_id = request.form.get('id')
        username = request.form.get('username')
        email = request.form.get('email')
        file = request.files.get('image')

        conn = get_db_connection()
        cursor = conn.cursor()

        image_url = None
        if file:
            original_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            file.save(file_path)
            image_url = original_filename

            cursor.execute(
                "UPDATE auth_flutter SET username=%s, email=%s, image=%s WHERE id=%s",
                (username, email, original_filename, user_id)
            )
        else:
            cursor.execute(
                "UPDATE auth_flutter SET username=%s, email=%s WHERE id=%s",
                (username, email, user_id)
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "image_url": image_url
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.json
        product_id = data.get('product_id')

        if not product_id:
            app.logger.error("Product ID not provided in the request body.")
            return jsonify({"success": False, "message": "Product ID is required"}), 400

        app.logger.info(f"Received request to add product {product_id} to cart")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM auth_flutter WHERE is_login = TRUE LIMIT 1")
        user = cursor.fetchone()

        if not user:
            app.logger.error("No logged-in user found.")
            return jsonify({"success": False, "message": "No logged-in user found"}), 401

        user_id = user['id']
        app.logger.info(f"Logged-in user ID: {user_id}")

        cursor.execute("SELECT id, name, price, image FROM product WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            app.logger.error(f"Product with ID {product_id} not found in the database.")
            return jsonify({"success": False, "message": "Product not found"}), 404

        cursor.execute(
            "SELECT id, quantity FROM cartitem WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        cart_item = cursor.fetchone()

        if cart_item:
            new_quantity = cart_item['quantity'] + 1
            total_price = product['price'] * new_quantity
            cursor.execute(
                "UPDATE cartitem SET quantity = %s, total_price = %s, image = %s, product_name = %s WHERE id = %s",
                (new_quantity, total_price, product['image'], product['name'], cart_item['id'])
            )
            app.logger.info(f"Updated quantity and total price for product {product_id} in cart.")
        else:
            total_price = product['price']
            cursor.execute(
                "INSERT INTO cartitem (user_id, product_id, quantity, price, total_price, image, product_name) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, product_id, 1, product['price'], total_price, product['image'], product['name'])
            )
            app.logger.info(f"Added new product {product_id} to cart.")

        conn.commit()

        app.logger.info(f"Product {product_id} added to cart successfully.")

        return jsonify({
            "success": True,
            "message": "Product added to cart",
            "product": {
                "id": product['id'],
                "name": product['name'],
                "price": product['price'],
                "quantity": cart_item['quantity'] + 1 if cart_item else 1,
                "total_price": total_price,
                "image": product['image'],
                "product_name": product['name']
            },
        }), 200

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/get_cart_items', methods=['GET'])
def get_cart_items():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM auth_flutter WHERE is_login = TRUE LIMIT 1")
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "No logged-in user found"}), 401

        user_id = user['id']

        cursor.execute("""
                    SELECT c.id, p.name AS product_name, p.image, c.product_id, c.quantity, p.price, c.total_price
                        FROM cartitem c
                        JOIN product p ON c.product_id = p.id
                        WHERE c.user_id = %s

                """, (user_id,))

        cart_items = cursor.fetchall()

        if cart_items:
            return jsonify({"success": True, "cart_items": cart_items}), 200
        else:
            return jsonify({"success": False, "message": "No items in the cart"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/update_cart_item', methods=['POST'])
def update_cart_item():
    print(request.json)
    try:
        data = request.json
        product_id = data.get('product_id')
        action = data.get('action')

        if not product_id or not action:
            return jsonify({"success": False, "message": "Product ID and action are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM auth_flutter WHERE is_login = TRUE LIMIT 1")
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "No logged-in user found"}), 401

        user_id = user['id']

        cursor.execute(
            "SELECT id, quantity, price, total_price FROM cartitem WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        cart_item = cursor.fetchone()

        if not cart_item:
            return jsonify({"success": False, "message": "Cart item not found"}), 404

        if action == 'increment':
            new_quantity = cart_item['quantity'] + 1
        elif action == 'decrement':
            new_quantity = cart_item['quantity'] - 1
        else:
            return jsonify({"success": False, "message": "Invalid action"}), 400

        if new_quantity > 0:
            new_total_price = new_quantity * cart_item['price']
            cursor.execute(
                "UPDATE cartitem SET quantity = %s, total_price = %s WHERE id = %s",
                (new_quantity, new_total_price, cart_item['id'])
            )
            message = "Cart item updated"
        else:
            cursor.execute("DELETE FROM cartitem WHERE id = %s", (cart_item['id'],))
            message = "Cart item removed"

        conn.commit()

        return jsonify({
            "success": True,
            "message": message,
            "product_id": product_id,
            "quantity": new_quantity if new_quantity > 0 else 0
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/create_order_after_payment', methods=['POST'])
def create_order_after_payment():
    """
    Saves the order to the database after a successful payment.
    This is called after a successful payment confirmation.
    """
    try:
        data = request.json
        items = data.get('items', [])
        total_price = data.get('total_price', 0.0)
        payment_success = data.get('payment_success', False)

        if not items:
            return jsonify({"success": False, "message": "Order items are required"}), 400
        if not payment_success:
            return jsonify({"success": False, "message": "Payment was not successful"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM auth_flutter WHERE is_login = TRUE LIMIT 1")
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "No logged-in user found"}), 401

        user_id = user['id']

        cursor.execute(
            "INSERT INTO orders (user_id, total_price, order_date) VALUES (%s, %s, NOW())",
            (user_id, total_price)
        )
        order_id = cursor.lastrowid

        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            product_name = item.get('product_name')

            if not product_id or not quantity:
                return jsonify({"success": False, "message": "Product ID and quantity are required for each item"}), 400

            cursor.execute("SELECT price FROM product WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if not product:
                return jsonify({"success": False, "message": f"Product with ID {product_id} not found"}), 404

            price = product['price']
            total_item_price = price * quantity

            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, quantity, price, total_price) "
                "VALUES (%s, %s, %s,%s, %s, %s)",
                (order_id, product_id,product_name, quantity, price, total_item_price)
            )

        cursor.execute("DELETE FROM cartitem WHERE user_id = %s", (user_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order_id": order_id
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/get_orders/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    """
    Fetches the orders for a specific user by user ID.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC", (user_id,))
        orders = cursor.fetchall()

        if not orders:
            return jsonify({"success": True, "orders": []}), 200

        order_data = []
        for order in orders:
            cursor.execute(
                "SELECT oi.product_id, p.name as product_name, oi.quantity, oi.price, oi.total_price "
                "FROM order_items oi "
                "JOIN product p ON oi.product_id = p.id "
                "WHERE oi.order_id = %s",
                (order['id'],)
            )
            items = cursor.fetchall()

            total_items_count = sum(item['quantity'] for item in items)

            order_data.append({
                "order_id": order['id'],
                "total_price": order['total_price'],
                "total_items_count": total_items_count,
                "order_date": order['order_date'],
                "items": items
            })

        return jsonify({"success": True, "orders": order_data}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


@app.route('/profile_image/<filename>')
def serve_profile_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
