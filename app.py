from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from PIL import Image
import webbrowser
from threading import Timer
from werkzeug.utils import secure_filename
import uuid
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuration for image uploads
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max file size: 5MB
app.secret_key = 'supersecretkey'  # Required for flashing messages

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
RECIPES_PER_PAGE_DEFAULT = 5  # Default number of recipes per page

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthorized users to login page

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Load user by ID
@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(id=user[0], username=user[1])
    return None

# Database setup
def init_db():
    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL
                        )''')
        
        # Create recipes table with a foreign key reference to users
        cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            ingredients TEXT NOT NULL,
                            instructions TEXT NOT NULL,
                            image TEXT,
                            user_id INTEGER NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )''')

        # Create ratings table with references to users and recipes
        cursor.execute('''CREATE TABLE IF NOT EXISTS ratings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            recipe_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                            FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )''')
        
        # Create comments table with references to users and recipes
        cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            recipe_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            comment TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )''')

        conn.commit()

# Check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to delete an image file
def delete_image(filename):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(image_path):
        os.remove(image_path)

@app.route('/dashboard')
@login_required
def dashboard():
    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE user_id = ?", (current_user.id,))
        user_recipes = cursor.fetchall()
    
    return render_template("dashboard.html", recipes=user_recipes)

# Home route with pagination and search functionality
@app.route('/')
def home():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)  # Current page number, default is 1
    per_page = request.args.get('per_page', RECIPES_PER_PAGE_DEFAULT, type=int)  # Get recipes per page, default to 5
    
    offset = (page - 1) * per_page  # Calculate offset

    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        if query:
            # Filtered search with pagination
            cursor.execute("""
                SELECT * FROM recipes 
                WHERE title LIKE ? COLLATE NOCASE OR ingredients LIKE ? COLLATE NOCASE
                LIMIT ? OFFSET ?
            """, ('%' + query + '%', '%' + query + '%', per_page, offset))
            recipes = cursor.fetchall()

            # Count total filtered recipes for pagination
            cursor.execute("""
                SELECT COUNT(*) FROM recipes 
                WHERE title LIKE ? COLLATE NOCASE OR ingredients LIKE ? COLLATE NOCASE
            """, ('%' + query + '%', '%' + query + '%'))
            total_recipes = cursor.fetchone()[0]
        else:
            # Unfiltered query with pagination
            cursor.execute("SELECT * FROM recipes LIMIT ? OFFSET ?", (per_page, offset))
            recipes = cursor.fetchall()

            # Count total recipes for pagination
            cursor.execute("SELECT COUNT(*) FROM recipes")
            total_recipes = cursor.fetchone()[0]

    # Calculate total pages
    total_pages = (total_recipes + per_page - 1) // per_page

    return render_template("home.html", recipes=recipes, page=page, total_pages=total_pages, per_page=per_page, query=query)

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        with sqlite3.connect("recipe.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                flash("Registration successful! Please log in.")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Username already exists. Please choose a different one.")
                return redirect(request.url)

    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("recipe.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                user_obj = User(id=user[0], username=user[1])
                login_user(user_obj)
                flash("Login successful!")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password.")
                return redirect(request.url)

    return render_template('login.html') 

# User Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('home'))

# Add new recipe route
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image = request.files['image']
        user_id = current_user.id

        if not title or not ingredients or not instructions:
            flash("All fields are required!")
            return redirect(request.url)

        if image and allowed_file(image.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image.save(image_path)

            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img = img.resize((300, 200))
                img.save(image_path)

            with sqlite3.connect("recipe.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO recipes (title, ingredients, instructions, image, user_id) VALUES (?, ?, ?, ?, ?)", 
                               (title, ingredients, instructions, filename, user_id))
                conn.commit()

            flash("Recipe added successfully.")
            return redirect(url_for('home'))
        else:
            flash("Invalid image format. Only PNG, JPG, JPEG, and WEBP are allowed.")
            return redirect(request.url)
    return render_template("add_recipe.html")

# View individual recipe route
@app.route('/recipe/<int:id>')
def recipe(id):
    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()

        # Fetch the recipe details
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (id,))
        recipe = cursor.fetchone()

        # Calculate the average rating
        cursor.execute("SELECT AVG(rating) FROM ratings WHERE recipe_id = ?", (id,))
        avg_rating = cursor.fetchone()[0]
        avg_rating = round(avg_rating, 1) if avg_rating else "No ratings yet"

        # Fetch comments
        cursor.execute("""
            SELECT comments.comment, comments.created_at, users.username 
            FROM comments 
            JOIN users ON comments.user_id = users.id 
            WHERE comments.recipe_id = ? 
            ORDER BY comments.created_at DESC
        """, (id,))
        comments = cursor.fetchall()

    return render_template("recipe.html", recipe=recipe, avg_rating=avg_rating, comments=comments)

# Rate recipe route
@app.route('/recipe/rate/<int:recipe_id>', methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    rating = int(request.form.get('rating'))
    
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.")
        return redirect(url_for('recipe', id=recipe_id))

    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()

        # Check if the user has already rated this recipe
        cursor.execute("SELECT * FROM ratings WHERE recipe_id = ? AND user_id = ?", (recipe_id, current_user.id))
        existing_rating = cursor.fetchone()

        if existing_rating:
            # Update the existing rating
            cursor.execute("UPDATE ratings SET rating = ? WHERE recipe_id = ? AND user_id = ?", (rating, recipe_id, current_user.id))
            flash("Your rating has been updated.")
        else:
            # Insert a new rating
            cursor.execute("INSERT INTO ratings (recipe_id, user_id, rating) VALUES (?, ?, ?)", (recipe_id, current_user.id, rating))
            flash("Your rating has been submitted.")

        conn.commit()

    return redirect(url_for('recipe', id=recipe_id))

# Comment recipe route
@app.route('/recipe/comment/<int:recipe_id>', methods=['POST'])
@login_required
def comment_recipe(recipe_id):
    comment_text = request.form.get('comment')

    if not comment_text:
        flash("Comment cannot be empty.")
        return redirect(url_for('recipe', id=recipe_id))

    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (recipe_id, user_id, comment) VALUES (?, ?, ?)", (recipe_id, current_user.id, comment_text))
        conn.commit()

    flash("Your comment has been added.")
    return redirect(url_for('recipe', id=recipe_id))

# Edit recipe route
@app.route('/recipe/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(id):
    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE id = ? AND user_id = ?", (id, current_user.id))
        recipe = cursor.fetchone()

    if not recipe:
        flash("You do not have permission to edit this recipe.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image = request.files['image']

        if not title or not ingredients or not instructions:
            flash("All fields are required!")
            return redirect(request.url)

        # Set filename to the current image filename by default
        filename = recipe[4]

        # If a new image is uploaded, process it
        if image and allowed_file(image.filename):
            # Delete the old image if it exists
            if filename:
                delete_image(filename)

            # Generate a unique filename for the new image
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save and resize the new image
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image.save(image_path)

            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img = img.resize((300, 200))
                img.save(image_path)

        # Update the recipe in the database
        with sqlite3.connect("recipe.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE recipes SET title = ?, ingredients = ?, instructions = ?, image = ? WHERE id = ?", 
                           (title, ingredients, instructions, filename, id))
            conn.commit()

        flash("Recipe updated successfully.")
        return redirect(url_for('recipe', id=id))

    return render_template("edit_recipe.html", recipe=recipe)

# Delete recipe route
@app.route('/recipe/delete/<int:id>', methods=['POST'])
@login_required
def delete_recipe(id):
    with sqlite3.connect("recipe.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE id = ? AND user_id = ?", (id, current_user.id))
        recipe = cursor.fetchone()

        if not recipe:
            flash("You do not have permission to delete this recipe.")
            return redirect(url_for('home'))

        # Delete the image associated with the recipe, if it exists
        if recipe[4]:
            delete_image(recipe[4])

        cursor.execute("DELETE FROM recipes WHERE id = ?", (id,))
        conn.commit()

    flash("Recipe deleted successfully.")
    return redirect(url_for('home'))

# Function to open the browser only when the Flask reloader is not active
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# Run the app
if __name__ == '__main__':
    init_db()
    # Open the browser
    Timer(1, open_browser).start()
    app.run(debug=True, use_reloader=False)
