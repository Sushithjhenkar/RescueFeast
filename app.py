from flask import Flask, render_template, request,session, redirect, g
import sqlite3

app = Flask(__name__)
app.secret_key = '69'
app.database = "portal.db"


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          username TEXT, 
                          password TEXT, 
                          role TEXT)''')
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Add 'email' column if it doesn't exist
        if 'email' not in column_names:
            cursor.execute('''ALTER TABLE users
                              ADD COLUMN email TEXT''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS food_items
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          food_name TEXT, 
                          food_quantity INTEGER,
                          food_type TEXT, 
                          food_address TEXT, 
                          status TEXT)''')
        cursor.execute("PRAGMA table_info(food_items)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        if 'pickup_instructions' not in column_names:
            # Add the new column if it doesn't exist
            cursor.execute('''ALTER TABLE food_items
                                      ADD COLUMN pickup_instructions TEXT''')
        if 'food_expiry_date' not in column_names:
            # Add the new column if it doesn't exist
            cursor.execute('''ALTER TABLE food_items
                                              ADD COLUMN food_expiry_date DATE''')
        if 'accepted_by' not in column_names:
            # Add the new column if it doesn't exist
            cursor.execute('''ALTER TABLE food_items
                                              ADD COLUMN accepted_by TEXT''')
        db.commit()
        db.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.database)
    return db


def insert_user(username, password, role, email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)", (username, password, role, email))
    db.commit()


def check_credentials(username, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    return user


def get_user_by_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    return user


def get_food_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM food_items WHERE status='pending'")
    food_items = cursor.fetchall()
    return food_items


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        email = request.form['email']
        insert_user(username, password, role, email)
        return redirect('/login')
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_credentials(username, password)
        if user:
            session['user_id'] = user[0]
            session['role'] = user[3]  # Store the user's role in the session
            if user[3] == 'donor':
                return redirect('/donor_dashboard')
            elif user[3] == 'volunteer':
                return redirect('/volunteer_dashboard')
        else:
            return render_template('login.html', message='Invalid credentials. Please try again.')
    return render_template('login.html')


from flask import jsonify

@app.route('/delete/<int:item_id>', methods=['DELETE'])
def delete_food_item(item_id):
    if request.method == 'DELETE':
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM food_items WHERE id=?", (item_id,))
        db.commit()
        db.close()

        return jsonify({'message': 'Item deleted successfully'})
    else:
        return jsonify({'error': 'Method not allowed'}), 405


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user = get_user_by_id(user_id)
        if user:
            if user[3] == 'donor':
                return redirect('/donor_dashboard')
            elif user[3] == 'volunteer':
                return redirect('/volunteer_dashboard')
    return redirect('/login')


@app.route('/donor_home')
def donor_home():
    return render_template('donor_dashboard.html')


@app.route('/donor_dashboard')
def donor_dashboard():
    return render_template('donor_dashboard.html')


@app.route('/volunteer_dashboard')
def volunteer_dashboard():
    if 'user_id' in session:
        accepted_food_items = get_accepted_food_items()
        rejected_food_items = get_rejected_food_items()
        food_items = get_food_items()
        return render_template('volunteer_dashboard.html', food_items=food_items, accepted_food_items=accepted_food_items, rejected_food_items=rejected_food_items)
    return redirect('/login')


@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/donate')
def donate():
    return render_template('donor_add_food.html')


@app.route('/volunteer_requests')
def volunteer_requests():
    # accepted_food_items = get_accepted_food_items()
    # rejected_food_items = get_rejected_food_items()
    food_items = get_food_items()
    return render_template('volunteer_food_requests.html', food_items=food_items)

@app.route('/requests')
def requests():
    if 'user_id' in session:
        user_id = session['user_id']
        user = get_user_by_id(user_id)
        if user:
            if user[3] == 'donor':
                return redirect('/donor_requests')
            elif user[3] == 'volunteer':
                return redirect('/volunteer_requests')  # Redirect to the appropriate route for volunteers
    return redirect('/login')  # Redirect to the login page if user is not authenticated

@app.route('/accept')
def accept():
    accepted_food_items = get_accepted_food_items()
    rejected_food_items = get_rejected_food_items()
    return render_template('volunteer.html',accepted_food_items=accepted_food_items, rejected_food_items=rejected_food_items)


@app.route('/logout')
def logout():
    session.clear()  # Clear the session data
    return redirect('/')  # Redirect to the index page


@app.route('/donor', methods=['GET', 'POST'])
def donor_portal():
    if request.method == 'POST':
        food_name = request.form['food_name']
        food_quantity = request.form['food_quantity']
        food_address = request.form['food_address']
        food_type = request.form['food_type']
        food_expiry_date = request.form['food_expiry_date']
        pickup_instructions = request.form['pickup_instructions']
        status = 'pending'
        add_food_item(food_name, food_quantity, food_address, food_type, food_expiry_date, pickup_instructions, status)
    return render_template('donor.html')



@app.route('/volunteer')
def volunteer():
    food_items = get_food_items()
    return render_template('volunteer.html', food_items=food_items)

def add_food_item(food_name, food_quantity, food_address, food_type, food_expiry_date, pickup_instructions, accepted_by=None, status='pending'):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO food_items (food_name, food_quantity, food_address, food_type, food_expiry_date, pickup_instructions, accepted_by, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (food_name, food_quantity, food_address, food_type, food_expiry_date, pickup_instructions, accepted_by, status))
    db.commit()



@app.route('/accept/<int:item_id>')
def accept_food(item_id):
    accepted_user_id = session.get('user_id')  # Assuming you store user_id in the session
    update_status(item_id, 'accepted', accepted_user_id)
    return redirect('/accept')


def get_accepted_food_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, food_name, food_quantity, food_address, food_type, food_expiry_date, pickup_instructions, accepted_by FROM food_items WHERE status='accepted'")
    accepted_food_items = cursor.fetchall()
    return accepted_food_items


def get_all_food_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM food_items")
    all_food_items = cursor.fetchall()
    return all_food_items

@app.route('/donor_requests')
def donor_requests():
    # Retrieve all food items
    food_items = get_all_food_items()
    return render_template('donor_requests.html', get_all_food_items=food_items)

def get_rejected_food_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, food_name, food_quantity, food_address, food_type, food_expiry_date, pickup_instructions FROM food_items WHERE status='rejected'")
    rejected_food_items = cursor.fetchall()
    return rejected_food_items



@app.route('/reject/<int:item_id>')
def reject_food(item_id):
    update_status(item_id, 'rejected', accepted_by=None)
    return redirect('/accept')


def update_status(item_id, status, accepted_by=None):
    db = get_db()
    cursor = db.cursor()
    if accepted_by:
        cursor.execute("UPDATE food_items SET status=?, accepted_by=? WHERE id=?", (status, accepted_by, item_id))
    else:
        cursor.execute("UPDATE food_items SET status=? WHERE id=?", (status, item_id))
    db.commit()



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
