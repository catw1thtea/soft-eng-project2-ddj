import os
from datetime import datetime, timezone

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)



from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash




load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DBNAME", "filmreviews")]

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, doc):
        self.id = str(doc["_id"])
        self.username = doc["username"]


@login_manager.user_loader
def load_user(user_id):
    doc = db.users.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None


#authentication

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        
        if not username or not password:
            flash("Username and password are required.")
        elif db.users.find_one({"username": username}):
            flash("That username is taken.")
        else:
            result = db.users.insert_one(
                {"username": username, "password": generate_password_hash(password)}
            )
            login_user(User({"_id": result.inserted_id, "username": username}))
            return redirect(url_for("feed"))


        
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        doc = db.users.find_one({"username": request.form["username"].strip()})
        if doc and check_password_hash(doc["password"], request.form["password"]):
            login_user(User(doc))
            return redirect(url_for("feed"))
        flash("Wrong username or password.")


        
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# Data page

@app.route("/")
@login_required
def feed():
    reviews = list(db.reviews.find().sort("created_at", -1).limit(50))


    
    return render_template("feed.html", reviews=reviews)


# reviews

@app.route("/write", methods=["GET", "POST"])
@login_required
def write():
    films = list(db.films.find().sort("title", 1))
    if request.method == "POST":
        film = db.films.find_one({"_id": ObjectId(request.form["film_id"])})
        rating = int(request.form["rating"])
        text = request.form["text"].strip()
        if not film or not 1 <= rating <= 5 or not text:
            flash("Pick a film, a rating from 1 to 5, and write something.")
        else:
            db.reviews.insert_one(
                {

                    
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "film_id": str(film["_id"]),
                    "film_title": film["title"],

                    
                    "rating": rating,
                    "text": text,


                    
                    "created_at": datetime.now(timezone.utc),
                }
            )
            return redirect(url_for("film", film_id=str(film["_id"])))
    return render_template(
        "write.html", films=films, selected=request.args.get("film_id", "")
    )


# films


def film_stats(film_id):
    """Return (average rating rounded to 1 decimal, review count) for a film."""
    pipeline = [
        {"$match": {"film_id": film_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    rows = list(db.reviews.aggregate(pipeline))
    if not rows:
        return None, 0
    return round(rows[0]["avg"], 1), rows[0]["count"]


@app.route("/film/<film_id>")
@login_required
def film(film_id):
    try:
        doc = db.films.find_one({"_id": ObjectId(film_id)})
    except Exception:
        doc = None
    if not doc:
        flash("That film doesn't exist.")
        return redirect(url_for("feed"))
    reviews = list(db.reviews.find({"film_id": film_id}).sort("created_at", -1))
    avg, count = film_stats(film_id)
    return render_template("film.html", film=doc, reviews=reviews, avg=avg, count=count)




if __name__ == "__main__":
    app.run(debug=True, port=5000)
