from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    session,
)
import os
import json
from werkzeug.utils import secure_filename

# ------------------ Flask App ------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "assets"
ALLOWED_EXTENSIONS = {"mp3", "mp4"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------ Gestion utilisateurs ------------------
USERS_FILE = "users.json"
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
else:
    USERS = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)

# ------------------ Favoris ------------------
FAVORITES_FILE = "favorites.json"
if os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, "r") as f:
        try:
            favorites_db = json.load(f)
        except json.JSONDecodeError:
            favorites_db = {}
else:
    favorites_db = {}

def save_favorites():
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites_db, f)

# ------------------ Vérifier fichiers ------------------
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        and filename.count(".") == 1
    )

# ------------------ Routes ------------------
@app.route("/")
def index():
    user = session.get("username")
    favs = favorites_db.get(user, []) if user else []
    return render_template("index.html", favorites=favs)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        flash("Vous devez être connecté.")
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Aucun fichier sélectionné.")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Extension non autorisée.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        flash("Fichier uploadé avec succès.")
        return redirect(url_for("upload"))

    return render_template("upload.html")
@app.route("/playlist")
def playlist():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if allowed_file(f)
    ]
    return render_template("playlist.html", files=files)


@app.route("/assets/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session["username"] = username
            flash(f"Bienvenue {username}!")
            return redirect(url_for("index"))
        else:
            flash("Identifiants invalides.")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Veuillez remplir tous les champs.")
            return redirect(url_for("register"))
        if username in USERS:
            flash("Ce nom d'utilisateur existe déjà.")
            return redirect(url_for("register"))
        USERS[username] = password
        save_users()
        session["username"] = username
        flash("Compte créé et connecté avec succès.")
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/visualizer")
def visualizer():
    return render_template("visualizer.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Déconnecté avec succès.")
    return redirect(url_for("index"))

@app.route("/add_favorite/<filename>")
def add_favorite(filename):
    if "username" not in session:
        flash("Vous devez être connecté.")
        return redirect(url_for("login"))
    user = session["username"]
    favorites_db.setdefault(user, [])
    if filename not in favorites_db[user]:
        favorites_db[user].append(filename)
        save_favorites()
        flash(f"{filename} ajouté aux favoris.")
    else:
        flash(f"{filename} est déjà dans vos favoris.")
    return redirect(url_for("playlist"))

@app.route("/search", methods=["GET", "POST"])
def search():
    query = ""
    results = []
    if request.method == "POST":
        query = request.form.get("query", "").lower()
        files = [
            f
            for f in os.listdir(UPLOAD_FOLDER)
            if f.split(".")[-1].lower() in ALLOWED_EXTENSIONS
        ]
        results = [f for f in files if query in f.lower()]
    return render_template("search.html", results=results, query=query)

@app.route("/favorites")
def show_favorites():
    if "username" not in session:
        return redirect(url_for("login"))
    user = session["username"]
    favs = favorites_db.get(user, [])
    return render_template("favorites.html", favorites=favs)

# ------------------ Lancer ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
