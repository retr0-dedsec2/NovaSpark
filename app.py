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
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(
    "./novaspark7-8f86a-firebase-adminsdk-fbsvc-34532a70d7.json"
)
firebase_admin.initialize_app(cred)
db = firestore.client()


app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "assets"
ALLOWED_EXTENSIONS = {"mp3", "mp4"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- Gestion des utilisateurs JSON ----------
USERS_FILE = "users.json"

# Configuration de l'API Spotify
SPOTIPY_CLIENT_ID = "e76c1b848bf849d99341e30d6bc4e62d"
SPOTIPY_CLIENT_SECRET = "c3d76edb497347aabcf1776ae21fe002"
SPOTIPY_REDIRECT_URI = "http://192.168.1.72:5000/callback"
SCOPE = "user-library-read"
# Initialisation de l'API Spotify
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
    )
)

# Charger les utilisateurs depuis le JSON
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
else:
    USERS = {}


# Sauvegarder les utilisateurs dans le JSON
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)


# ---------- Gestion des favoris ----------
favorites_db = {}


# ---------- Fonctions utilitaires ----------
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        and filename.count(".") == 1
    )


# ---------- Routes ----------
@app.route("/")
def index():
    if "username" in session:
        user = session["username"]
        favs = favorites_db.get(user, [])
    else:
        favs = []
    return render_template("index.html", favorites=favs)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        flash("Vous devez être connecté.")
        return redirect(url_for("login"))
    UPLOADS[filename] = session["username"]
    with open(UPLOADS_FILE, "w") as f:
        json.dump(UPLOADS, f)
    if request.method == "POST":
        if "file" not in request.files:
            flash("Aucun fichier sélectionné.")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("Aucun fichier sélectionné.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            flash("Fichier uploadé avec succès.")
            return redirect(url_for("upload"))
        else:
            flash("Nom invalide ou extension interdite.")
            return redirect(request.url)
    return render_template("upload.html")


@app.route("/callback")
def callback():
    token_info = sp.auth_manager.get_access_token()
    if token_info:
        session["token_info"] = token_info
        flash("Vous êtes maintenant connecté à Spotify.")
    else:
        flash("Échec de la connexion à Spotify.")
    return redirect(url_for("index"))


@app.route("/playlist")
def playlist():
    files = [
        f
        for f in os.listdir(UPLOAD_FOLDER)
        if f.split(".")[-1].lower() in ALLOWED_EXTENSIONS
    ]
    return render_template("playlist.html", files=files, uploads=UPLOADS)


@app.route("/assets/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


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


@app.route("/search_spotify", methods=["GET", "POST"])
def search_spotify():
    results = []
    if request.method == "POST":
        query = request.form.get("query")
        results = sp.search(q=query, type="track", limit=10)
    return render_template("search_spotify.html", results=results)


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
    print("DEBUG SESSION:", session)
    if "username" not in session:
        flash("Vous devez être connecté.")
        return redirect(url_for("login"))
    user = session["username"]
    print("DEBUG USER:", user)
    favorites_db.setdefault(user, [])
    if filename not in favorites_db[user]:
        favorites_db[user].append(filename)
        flash(f"{filename} ajouté aux favoris.")
    else:
        flash(f"{filename} est déjà dans vos favoris.")
    return redirect(url_for("playlist"))


@app.route("/favorites")
def show_favorites():
    if "username" not in session:
        return redirect(url_for("login"))
    user = session["username"]
    favs = favorites_db.get(user, [])
    return render_template("favorites.html", favorites=favs)


UPLOADS_FILE = "uploads.json"

# Charger l'historique des uploads
if os.path.exists(UPLOADS_FILE):
    with open(UPLOADS_FILE, "r") as f:
        UPLOADS = json.load(f)
else:
    UPLOADS = {}


# ---------- Lancer l'application ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
