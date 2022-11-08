import random
from functools import wraps

import pandas as pd
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_compress import Compress
from flask_gravatar import Gravatar
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from requests import Session
from sqlalchemy.orm import relationship
from unidecode import unidecode
from werkzeug.security import check_password_hash, generate_password_hash

from static.scripts.functions import (differ_by_single_char, empty,
                                      has_only_allowed_symbols, is_valid_email)

# ! Remember to add the module to the requirements.txt file


app = Flask(__name__)
Compress(app)
app.config['SECRET_KEY'] = "caF^GdASSz%QJZwT2001*^"
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(
    app, size=100, rating='g', default='retro',
    force_default=False, force_lower=False, use_ssl=False, base_url=None
)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):  # type: ignore
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)


db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:  # type: ignore
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.template_filter('decode')
def decode(string_to_decode):
    return unidecode(string_to_decode)


topics = ["_environment", "a1l7", "health-diseases",
          "people-body", "people-face", "people-hand"]
verbs = [
    "abitare", "andare", "avere", "capire", "dare", "dire", "dormire", "dovere", "essere", "fare",
    "finire", "leggere", "parlare", "potere", "sapere", "stare", "trovare", "uscire", "vedere", "venire", "volere"
]
lessons_list = ["the alphabet"]  # type: ignore


@app.route('/')
def index():
    return render_template(
        'index.html',
        current_user=current_user,
        topics=topics,
        verbs=verbs,
        lessons_list=lessons_list
    )


@app.route('/vocabulary_topics')
def vocabulary_topics():
    return render_template("vocabulary_topics.html", current_user=current_user)


@app.route('/lessons')
def lessons():
    return render_template("lessons.html", current_user=current_user)


@app.route('/lesson_for_topic/<topic>')
def lesson_for_topic(topic):
    return render_template(f"lessons/{topic}.html", current_user=current_user)


@app.route('/conjugation_drill_tenses')
def conjugation_drill_tenses():
    return render_template("conjugation_drill_tenses.html", current_user=current_user)


@app.route('/conjugation_drill_for_tense/<tense>')
def conjugation_drill_for_tense(tense):
    return render_template("conjugation_drill_for_tense.html", tense=tense, current_user=current_user)


@app.route('/conjugation_drill_for_verb/<tense>/<verb>', methods=["GET", "POST"])
def conjugation_drill_for_verb(tense, verb):
    def set_random_verb():  # Setting a random word to the session
        words = pd.read_csv(f"static/data/verbs/{verb}.csv")
        words = words.values.tolist()

        random_sentence = random.choice(words)

        session["pronoun"] = random_sentence[0]
        index = 0
        if tense == "presente":
            index = 1
        elif tense == "futuro_semplice":
            index = 2

        session["conjugated_verb"] = random_sentence[index]
        session["verb_id"] = random_sentence[3]
        session["verb"] = verb

    # Checking if the topic is available
    if not tense in ["presente", "futuro_semplice"]:
        flash("Unknown tense: " + tense)
        return redirect("/conjugation_drill_tenses")

    # Checking if the verb is amongst the verbs: abitare andare avere capire dare dire dormire dovere essere fare finire leggere parlare potere sapere stare trovare uscire vedere venire volere
    if not verb in verbs:
        flash("Unknown verb: " + verb)
        return redirect("/conjugation_drill_tenses")

    if request.form.get("user_input") != None:
        user_input = unidecode(request.form.get(
            "user_input")).lower()  # type: ignore
        verb_is_correct = user_input == unidecode(
            session["conjugated_verb"]).lower()

        if differ_by_single_char(user_input, unidecode(session["conjugated_verb"])):
            flash("You missed one letter.")
            return render_template(
                'conjugation_drill_for_verb.html',
                tense=tense,
                verb_is_correct=verb_is_correct,
                user_input=user_input,
                current_user=current_user,
                play_audio=True,
            )
        return render_template(
            'conjugation_drill_for_verb.html',
            tense=tense,
            verb_is_correct=verb_is_correct,
            current_user=current_user,
            play_audio=True,
        )

    set_random_verb()
    return render_template(
        'conjugation_drill_for_verb.html',
        tense=tense,
        current_user=current_user
    )


@app.route('/vocabulary_for_topic/<topic>', methods=["GET", "POST"])
def vocabulary_for_topic(topic):

    def set_random_word():  # Setting a random word to the session
        words = pd.read_csv(f"static/data/vocabulary/{topic}.csv")
        words = words.values.tolist()

        random_word = random.choice(words)

        session["german"] = random_word[0]
        session["english"] = random_word[1]
        session["word_id"] = random_word[2]
        session["image"] = random_word[3]
        if session["image"] == "None":
            session["image"] = None

    # Checking if the topic is available
    if not topic in topics:
        flash("Unknown topic: " + topic)
        return redirect("/vocabulary_topics")

    if request.form.get("user_input") != None:
        user_input = unidecode(request.form.get(
            "user_input")).lower()  # type: ignore

        word_is_correct = user_input == (
            unidecode(session["german"]).lower() or
            user_input in unidecode(session["german"]).lower().split("||")
        )

        if differ_by_single_char(user_input, unidecode(session["german"])):
            flash("You missed one letter.")
            return render_template(
                'vocabulary_for_topic.html',
                topic=topic,
                word_is_correct=word_is_correct,
                user_input=user_input,
                current_user=current_user,
                play_audio=True
            )
        return render_template(
            'vocabulary_for_topic.html',
            topic=topic,
            word_is_correct=word_is_correct,
            current_user=current_user,
            play_audio=True
        )

    set_random_word()
    return render_template(
        'vocabulary_for_topic.html',
        topic=topic,
        current_user=current_user,
    )


@app.route('/vocabulary_unit/<unit>')
def vocabulary_unit(unit):
    return render_template(f"units/{unit}.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.form.get("submit"):
        # Getting the data and storing it in variables
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # Validating the data
        if User.query.filter_by(email=email).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('register'))

        if empty(email, username, password):
            flash("Don't leave fields empty!")
            return redirect(url_for('register'))

        if not has_only_allowed_symbols(username, password):
            flash("You used not allowed symbols!")
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash("Please provide a valid email!")
            return redirect(url_for('register'))

        # Adding the user if the data is valid
        new_user = User(
            email=email,
            username=username,
            password=generate_password_hash(
                password,  # type: ignore
                method='pbkdf2:sha256',
                salt_length=8
            )
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))

    return render_template("register.html", current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.form.get("submit"):
        email_or_username = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email_or_username).first()
        if not user:
            user = User.query.filter_by(username=email_or_username).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("Profile not found!")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):  # type: ignore
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('index'))
    return render_template("login.html", current_user=current_user)


@app.route('/profile')
def profile():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    return render_template("profile.html", current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.errorhandler(404)
def error_404(e):
    logout_user()
    return render_template("error_404.html")


@app.route('/offline.html')
def offline():
    return app.send_static_file('offline.html')


@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')


@app.route('/robots.txt')
def robots_txt():
    return app.send_static_file('robots.txt')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
