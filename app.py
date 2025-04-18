from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "sewsecure123")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

categories = ["maorial", "weddings", "general_alterations", "custom_jobs", "curtains"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("upload"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form["category"]
        file = request.files["file"]
        description = request.form.get("description", "")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            category_folder = os.path.join(app.config["UPLOAD_FOLDER"], category)
            os.makedirs(category_folder, exist_ok=True)
            file_path = os.path.join(category_folder, filename)
            file.save(file_path)

            # Save description
            desc_file = os.path.join(category_folder, "descriptions.json")
            descriptions = {}
            if os.path.exists(desc_file):
                with open(desc_file, "r") as f:
                    descriptions = json.load(f)
            descriptions[filename] = description
            with open(desc_file, "w") as f:
                json.dump(descriptions, f)

            flash("Upload successful!")
            return redirect(url_for(category))

        flash("Invalid file.")
    return render_template("upload.html", categories=categories)

# ✅ FIXED: Dynamic category routes using unique view functions and endpoints
def generate_category_view(category_name):
    def view():
        folder = os.path.join(app.config["UPLOAD_FOLDER"], category_name)
        os.makedirs(folder, exist_ok=True)
        images = [img for img in os.listdir(folder) if img.lower().endswith(('png', 'jpg', 'jpeg', 'gif'))]

        descriptions = {}
        desc_file = os.path.join(folder, "descriptions.json")
        if os.path.exists(desc_file):
            with open(desc_file, "r") as f:
                descriptions = json.load(f)

        return render_template(f"{category_name}.html", images=images, descriptions=descriptions)
    return view

# ✅ Register all routes with unique function names via endpoints
for category_name in categories:
    view_func = generate_category_view(category_name)
    app.add_url_rule(f"/{category_name}", endpoint=category_name, view_func=view_func)

if __name__ == "__main__":
    app.run(debug=True)
