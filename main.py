import csv
import os
import random
import secrets
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_compress import Compress
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError
from unidecode import unidecode
from werkzeug.security import check_password_hash, generate_password_hash

import conjugation
import functions

app = Flask(__name__)


def load_secret_key():
    # In production set the SECRET_KEY environment variable.
    # Locally a random key is generated once and kept in instance/secret_key.
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    os.makedirs(app.instance_path, exist_ok=True)
    key_path = os.path.join(app.instance_path, "secret_key")
    if not os.path.exists(key_path):
        with open(key_path, "w") as key_file:
            key_file.write(secrets.token_hex(32))
    with open(key_path) as key_file:
        return key_file.read().strip()


app.config["SECRET_KEY"] = load_secret_key()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///users.db"
)
# The CSRF token stays valid for the whole session, so a drill left open
# for a long time doesn't fail on the next answer.
app.config["WTF_CSRF_TIME_LIMIT"] = None

Compress(app)
CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

MIN_PASSWORD_LENGTH = 8
DATA_DIR = os.path.join(app.root_path, "data")

TOPICS = ["foods", "drinks", "fruits", "transport"]

LANGUAGES = {
    "italian": {
        "lessons": ["the_alphabet", "definite_articles"],
        "cities": ["rome", "venice", "milan"],
    },
    "german": {
        "lessons": ["the_alphabet"],
        "cities": ["berlin", "frankfurt", "munich", "leipzig"],
    },
    "spanish": {
        "lessons": ["the_alphabet"],
        "cities": ["malaga"],
    },
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def load_vocabulary(lang, topic):
    words = []
    for row in read_csv(os.path.join(DATA_DIR, lang, "vocabulary", f"{topic}.csv")):
        foreign, english, word_id, image = list(row.values())[:4]
        words.append(
            {
                "foreign": foreign,
                "english": english,
                "id": word_id,
                "image": None if image in ("", "None") else image,
            }
        )
    return words


# All drill data is read once at startup instead of on every request.
VOCABULARY = {
    lang: {topic: load_vocabulary(lang, topic) for topic in TOPICS}
    for lang in LANGUAGES
}


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    language = db.Column(db.String(10), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


def get_lang():
    if current_user.is_authenticated:
        return current_user.language
    return session.get("language")


def not_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


def logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


# Allows access when logged in or when a guest has picked a language
def language_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_lang() not in LANGUAGES:
            session.pop("language", None)
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_language():
    return dict(user_language=get_lang())


@app.template_filter("format")
def format(string_to_format):
    return string_to_format.replace("_", " ").capitalize()


def get_progress():
    return request.args.get("progress", 0, type=int)


def check_answer(user_input, answer):
    # Returns (is_correct, missed_one_letter)
    is_correct = unidecode(user_input) == unidecode(answer)
    return is_correct, functions.differ_by_single_char(user_input, answer)


def drill_row(drill, row_count, **expected):
    # Returns the row saved in the session if it belongs to this drill
    if not isinstance(drill, dict):
        return None
    if any(drill.get(key) != value for key, value in expected.items()):
        return None
    row = drill.get("row")
    if not isinstance(row, int) or not 0 <= row < row_count:
        return None
    return row


def hash_password(password):
    # Keeps the hash short enough for the existing 100-character column
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)


@app.route("/")
def index():
    lang = get_lang()
    if lang not in LANGUAGES:
        return render_template("index.html", current_user=current_user)
    config = LANGUAGES[lang]
    return render_template(
        "index.html",
        current_user=current_user,
        topics=TOPICS,
        lessons_list=config["lessons"],
        random_city=random.choice(config["cities"]),
    )


@app.route("/vocabulary_topics")
@language_required
def vocabulary_topics():
    return render_template("vocabulary_topics.html", current_user=current_user)


@app.route("/lessons")
@language_required
def lessons():
    return render_template(
        "lessons.html", lessons=LANGUAGES[get_lang()]["lessons"], current_user=current_user
    )


@app.route("/lesson_for_topic/<topic>")
@language_required
def lesson_for_topic(topic):
    lang = get_lang()
    if topic not in LANGUAGES[lang]["lessons"]:
        abort(404)
    return render_template(f"lessons/{lang}/{topic}.html", current_user=current_user)


def get_conjugation_settings(lang):
    saved = session.get("conjugation", {}).get(lang, {})
    return conjugation.clean_settings(
        lang,
        saved.get("forms", conjugation.DEFAULT_FORMS[lang]),
        saved.get("pronouns", conjugation.DEFAULT_PRONOUNS.get(lang, [])),
    )


@app.route("/conjugation_drill", methods=["GET", "POST"])
@language_required
def conjugation_drill():
    lang = get_lang()
    if request.method == "POST":
        forms, pronouns = conjugation.clean_settings(
            lang, request.form.getlist("forms"), request.form.getlist("pronouns")
        )
        if not forms:
            flash("Choose at least one verb form.")
            return redirect(url_for("conjugation_drill"))
        settings = dict(session.get("conjugation", {}))
        settings[lang] = {"forms": forms, "pronouns": pronouns}
        session["conjugation"] = settings
        # Remember the choice after the browser is closed
        session.permanent = True
        session.pop("conjugation_question", None)
        return redirect(url_for("conjugation_practice"))

    forms, pronouns = get_conjugation_settings(lang)
    return render_template(
        "conjugation_drill.html",
        groups=conjugation.FORM_GROUPS[lang],
        pronoun_options=conjugation.PRONOUN_OPTIONS.get(lang, []),
        selected_forms=forms,
        selected_pronouns=pronouns,
        current_user=current_user,
    )


# Old links from the home screen of the installed app
@app.route("/conjugation_drill_tenses")
def conjugation_drill_tenses():
    return redirect(url_for("conjugation_drill"))


@app.route("/conjugation_drill/practice", methods=["GET", "POST"])
@language_required
def conjugation_practice():
    lang = get_lang()
    progress = get_progress()
    forms, pronouns = get_conjugation_settings(lang)
    if not forms:
        return redirect(url_for("conjugation_drill"))

    # Only the question is kept in the session cookie, never the answer
    question = session.get("conjugation_question")
    accepted = None
    if isinstance(question, dict) and question.get("language") == lang:
        accepted = conjugation.answers(question)

    user_input = request.form.get("user_input")
    if request.method == "POST" and user_input is not None and accepted:
        verb_is_correct, missed_one_letter, answer = conjugation.check(
            user_input, accepted
        )
        if missed_one_letter:
            flash("You missed one letter.")
        elif verb_is_correct:
            progress += 1
        return render_template(
            "conjugation_practice.html",
            **conjugation_question_args(question),
            answer=answer,
            verb_is_correct=verb_is_correct,
            user_input=user_input if missed_one_letter else None,
            play_audio=True,
            progress=progress,
            current_user=current_user,
        )

    question = conjugation.pick_question(lang, forms, pronouns, previous=question)
    if question is None:
        flash("There is nothing to practise with these settings.")
        return redirect(url_for("conjugation_drill"))
    session["conjugation_question"] = question
    return render_template(
        "conjugation_practice.html",
        **conjugation_question_args(question),
        progress=progress,
        current_user=current_user,
    )


def conjugation_question_args(question):
    lang, form = question["language"], question["form"]
    audio = conjugation.audio_path(lang, form, question["verb"], question["person"])
    return dict(
        verb=question["verb"],
        form_label=conjugation.FORM_LABELS[lang][form],
        pronoun=conjugation.person_label(lang, form, question["person"]),
        audio_url=url_for("static", filename=audio) if audio else None,
    )


@app.route("/vocabulary_for_topic/<topic>", methods=["GET", "POST"])
@language_required
def vocabulary_for_topic(topic):
    lang = get_lang()
    progress = get_progress()

    if topic not in TOPICS:
        flash("Unknown topic: " + topic)
        return redirect(url_for("vocabulary_topics"))

    words = VOCABULARY[lang][topic]
    # Only the row number is kept in the session cookie, never the answer
    drill = session.get("word_drill")
    user_input = request.form.get("user_input")
    if (
        request.method == "POST"
        and user_input is not None
        and (row := drill_row(drill, len(words), lang=lang, topic=topic)) is not None
    ):
        word = words[row]
        word_is_correct, missed_one_letter = check_answer(user_input, word["foreign"])
        template_args = dict(
            topic=topic,
            word=word,
            word_is_correct=word_is_correct,
            current_user=current_user,
            play_audio=True,
        )
        if missed_one_letter:
            flash("You missed one letter.")
            return render_template(
                "vocabulary_for_topic.html",
                user_input=user_input,
                progress=progress,
                **template_args,
            )
        if word_is_correct:
            progress += 1
        return render_template(
            "vocabulary_for_topic.html", progress=progress, **template_args
        )

    row = random.randrange(len(words))
    session["word_drill"] = {"lang": lang, "topic": topic, "row": row}
    return render_template(
        "vocabulary_for_topic.html",
        topic=topic,
        word=words[row],
        current_user=current_user,
        progress=progress,
    )


@app.route("/register", methods=["GET", "POST"])
@not_logged_in
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        language = request.form.get("language")

        if functions.empty(email, username, password):
            flash("Don't leave fields empty!")
            return redirect(url_for("register"))

        if not functions.is_valid_email(email):
            flash("Please enter a valid email address.")
            return redirect(url_for("register"))

        if not functions.has_only_allowed_symbols(username):
            flash("Usernames can only contain letters, numbers and _.")
            return redirect(url_for("register"))

        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f"Your password must be at least {MIN_PASSWORD_LENGTH} characters.")
            return redirect(url_for("register"))

        if language not in LANGUAGES:
            flash("Please choose a language.")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("That username is taken, please choose another one.")
            return redirect(url_for("register"))

        new_user = User(
            email=email,
            username=username,
            password=hash_password(password),
            language=language,
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That email or username is already taken.")
            return redirect(url_for("register"))
        login_user(new_user, remember=True)
        return redirect(url_for("index"))

    return render_template("register.html", current_user=current_user)


@app.route("/create_session_profile/<language>")
def create_session_profile(language):
    if language in LANGUAGES:
        session["language"] = language
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
@not_logged_in
def login():
    if request.method == "POST":
        email_or_username = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = (
            User.query.filter_by(email=email_or_username).first()
            or User.query.filter_by(username=email_or_username).first()
        )

        if not user:
            flash("Profile not found!")
            return redirect(url_for("login"))
        if not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for("login"))
        login_user(user, remember=True)
        return redirect(url_for("index"))
    return render_template("login.html", current_user=current_user)


@app.route("/profile")
@logged_in
def profile():
    return render_template("profile.html", current_user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    session.pop("language", None)
    return redirect(url_for("index"))


@app.route("/delete_profile", methods=["POST"])
@logged_in
def delete_profile():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return redirect(url_for("index"))


@app.route("/change_password", methods=["POST"])
@logged_in
def change_password():
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    if not check_password_hash(current_user.password, old_password):
        flash("Old password is incorrect!")
        return redirect(url_for("profile"))
    if len(new_password) < MIN_PASSWORD_LENGTH:
        flash(f"Your password must be at least {MIN_PASSWORD_LENGTH} characters.")
        return redirect(url_for("profile"))
    current_user.password = hash_password(new_password)
    db.session.commit()
    flash("Password changed!")
    return redirect(url_for("profile"))


@app.route("/change_username", methods=["POST"])
@logged_in
def change_username():
    password = request.form.get("password", "")
    new_username = request.form.get("new_username", "").strip()
    if not check_password_hash(current_user.password, password):
        flash("Password incorrect, please try again.")
        return redirect(url_for("profile"))
    if not new_username or not functions.has_only_allowed_symbols(new_username):
        flash("Usernames can only contain letters, numbers and _.")
        return redirect(url_for("profile"))
    if User.query.filter(
        User.username == new_username, User.id != current_user.id
    ).first():
        flash("That username is taken, please choose another one.")
        return redirect(url_for("profile"))
    current_user.username = new_username
    db.session.commit()
    flash("Username changed!")
    return redirect(url_for("profile"))


@app.route("/change_language", methods=["POST"])
@logged_in
def change_language():
    new_language = request.form.get("new_language")
    if new_language not in LANGUAGES:
        flash("Language not changed!")
        return redirect(url_for("profile"))
    current_user.language = new_language
    db.session.commit()
    flash("Language changed!")
    return redirect(url_for("profile"))


@app.errorhandler(404)
def error_404(e):
    return render_template("error_404.html"), 404


@app.route("/service-worker.js")
def sw():
    return app.send_static_file("service-worker.js")


@app.route("/robots.txt")
def robots_txt():
    return app.send_static_file("robots.txt")


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True)
