import os
import re
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


def own_review_or_none(review_id):
    """Return the review only if it exists and belongs to the current user."""
    try:
        doc = db.reviews.find_one({"_id": ObjectId(review_id)})
    except Exception:
        return None
    if not doc or doc["user_id"] != current_user.id:
        return None
    return doc


@app.route("/review/<review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    review = own_review_or_none(review_id)
    if not review:
        flash("You can only edit your own reviews.")
        return redirect(url_for("feed"))
    if request.method == "POST":
        rating = int(request.form["rating"])
        text = request.form["text"].strip()
        if not 1 <= rating <= 5 or not text:
            flash("Pick a rating from 1 to 5 and write something.")
        else:
            db.reviews.update_one(
                {"_id": review["_id"]},
                {"$set": {"rating": rating, "text": text, "edited_at": datetime.now(timezone.utc)}},
            )
            return redirect(url_for("film", film_id=review["film_id"]))
    return render_template("edit.html", review=review)


@app.route("/review/<review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = own_review_or_none(review_id)
    if not review:
        flash("You can only delete your own reviews.")
        return redirect(url_for("feed"))
    db.reviews.delete_one({"_id": review["_id"]})
    flash("Review deleted.")
    return redirect(request.form.get("next") or url_for("feed"))


# films


def film_stats(film_id):
    """Return (average rating rounded to 1 decimal, review count) for a film."""
    pipeline = [
        {"$match": {"film_id": film_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    rows = list(db.reviews.aggregate(pipeline))
    if not rows or not rows[0]["count"] or rows[0]["avg"] is None:
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


# search


@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    films, reviews = [], []
    if q:
        pattern = {"$regex": re.escape(q), "$options": "i"}
        films = list(
            db.films.find(
                {"$or": [{"title": pattern}, {"genre": pattern}, {"director": pattern}]}
            ).sort("title", 1)
        )
        for f in films:
            f["avg"], f["count"] = film_stats(str(f["_id"]))
        reviews = list(db.reviews.find({"text": pattern}).sort("created_at", -1).limit(20))
    genres = sorted(g for g in db.films.distinct("genre") if g)
    return render_template("search.html", q=q, films=films, reviews=reviews, genres=genres)


# profiles


def render_profile(user_doc):
    reviews = list(db.reviews.find({"user_id": str(user_doc["_id"])}).sort("created_at", -1))
    avg_given = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else None
    return render_template(
        "profile.html",
        profile_user=user_doc,
        reviews=reviews,
        avg_given=avg_given,
        is_me=str(user_doc["_id"]) == current_user.id,
    )


@app.route("/profile")
@login_required
def profile():
    return render_profile(db.users.find_one({"_id": ObjectId(current_user.id)}))


@app.route("/user/<username>")
@login_required
def user_profile(username):
    doc = db.users.find_one({"username": username})
    if not doc:
        flash("No user called @" + username + ".")
        return redirect(url_for("feed"))
    return render_profile(doc)




if __name__ == "__main__":
    app.run(debug=True, port=5000)
