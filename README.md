# Recipe Sharing Application

A simple recipe-sharing application built with Flask, allowing users to create, view, edit, and delete recipes. Users can also rate and comment on recipes. This project demonstrates essential CRUD operations, user authentication, pagination, search functionality, and file upload handling with image resizing.

## Features

- **User Registration and Authentication**: Users can register, log in, and log out securely.
- **Recipe Management**: Logged-in users can add, edit, and delete their own recipes.
- **Search and Pagination**: Browse recipes with search and pagination functionality on the homepage.
- **Image Upload**: Users can upload images for each recipe, with image resizing handled automatically.
- **Recipe Interactions**: Users can rate recipes (1-5 stars) and leave comments.

## Technologies Used

- **Backend**: Flask
- **Frontend**: HTML, CSS (custom styling)
- **Database**: SQLite
- **File Handling**: PIL (Pillow) for image processing
- **Authentication**: Flask-Login for session management

## Getting Started

### Prerequisites

- Python 3.x
- Git (for version control)
- A virtual environment tool (optional but recommended)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/flask-recipe-sharing.git
   cd flask-recipe-sharing
2. **Set up a virtual environment:**
* On Linux:
```Bash
python3 -m venv venv
source venv/bin/activate
```

* On Windows: 
```Bash
venv\Scripts\activate
```
3. **Install dependencies:**
```Bash
pip install -r requirements.txt
```
4. **Initialize the database:**
Run the following command in the Python interpreter to create the database tables:
```Python
from app import init_db
init_db()
```
5. **Run the application:**
```Bash
flask run
```
By default, the app will run on http://127.0.0.1:5000.

**File Structure**
```Plaintext
.
├── app.py               # Main Flask application
├── requirements.txt     # Project dependencies
├── static/
│   ├── uploads/         # Uploaded images directory
│   └── style.css        # Custom styles
├── templates/
│   ├── base.html        # Base template with header and footer
│   ├── home.html        # Home page with recipes and search
│   ├── add_recipe.html  # Form for adding new recipes
│   ├── edit_recipe.html # Form for editing recipes
│   └── recipe.html      # Recipe detail page
└── README.md            # Project documentation
```
**Usage**
1. **Register a new account** by clicking the "Register" link.
2. **Log in** to start adding, editing, and deleting recipes.
3. **Add a recipe** by filling in the title, ingredients, instructions, and uploading an image.
4. **Browse and search recipes** on the homepage, with pagination controls.
5. **Rate and comment** on other users' recipes.

**Configuration**
You can configure settings like the upload folder and maximum file size in ```app.py```
```Python
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max file size: 5MB
```