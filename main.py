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

# ! Remember to add the module to the requirements.txt file


def trim(string_to_trim):
    trimmed_string = ""
    for word in string_to_trim.split(" "):
        if word:
            trimmed_string += word + " "
    return trimmed_string


def has_only_allowed_symbols(*args, allowed_symbols="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_@.-+0123456789"):
    for arg in args:
        for letter in arg:
            if not letter in allowed_symbols:
                return False
    return True


def empty(*args):
    for arg in args:
        if trim(arg) == "":
            return True
    return False


def skip_by_one_char(first, second, n):
    imbalance = 0
    a = 0
    b = 0
    i = 0
    while (i < n and imbalance <= 1):
        if (first[a] == second[b]):
            #  When both string character at position a and b is same
            a += 1
            b += 1
        else:
            a += 1
            imbalance += 1

        i += 1

    if (imbalance == 0):
        #  In case, last character is extra in first string
        return 1

    return imbalance


def differ_by_single_char(first, second):
    #  Get the size of given string
    n = len(first)
    m = len(second)
    imbalance = 0
    if (n == m):
        i = 0
        #  Case A when both string are equal size
        while (i < n and imbalance <= 1):
            if (first[i] != second[i]):
                imbalance += 1

            i += 1

    elif (n - m == 1 or m - n == 1):
        #  When one string contains extra character
        if (n > m):
            imbalance = skip_by_one_char(first, second, m)
        else:
            imbalance = skip_by_one_char(second, first, n)

    return imbalance == 1


def is_valid_email(email):
    if not "@" in email or not "." in email:
        return False
    if email.count("@") > 1:
        return False
    if email.index("@") > email.index("."):
        return False
    return True


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
    return User.query.get(int(user_id))  # type: ignore


class User(UserMixin, db.Model):  # type: ignore
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    language = db.Column(db.String(10), nullable=False)


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


topics = ["foods", "drinks", "fruits", "transport"]
verbs_italian = [
    "abitare", "andare", "avere", "capire", "dare", "dire", "dormire", "dovere", "essere", "fare",
    "finire", "leggere", "parlare", "potere", "sapere", "stare", "trovare", "uscire", "vedere", "venire", "volere"
]
verbs_german = [
    "sein", "haben"
]
verbs_spanish = [
    "ser", "estar", "haber"
]
lessons_list = ["the_alphabet"]  # type: ignore


@app.route('/')  # type: ignore
def index():
    if current_user.is_authenticated:  # type: ignore
        if current_user.language == "italian":  # type: ignore
            return render_template(
            'index.html',
            current_user=current_user,
            topics=topics,
            tenses=["Presente", "Futuro Semplice"],
            lessons_list=lessons_list
        )
        elif current_user.language == "german":  # type: ignore
            return render_template(
            'index.html',
            current_user=current_user,
            topics=topics,
            tenses=["Präsens", "Präteritum", "Perfekt", "Plusquamperfekt", "Futur I", "Futur II"],
            lessons_list=lessons_list
        )
        elif current_user.language == "spanish":  # type: ignore
            return render_template(
            'index.html',
            current_user=current_user,
            topics=topics,
            tenses=["Presente", "Futuro"],
            lessons_list=lessons_list
        )
    else:
        return render_template(
        'index.html',
        current_user=current_user,
    )


@app.route('/vocabulary_topics')
def vocabulary_topics():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    return render_template("vocabulary_topics.html", current_user=current_user)


@app.route('/lessons')
def lessons():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    return render_template(f"lessons_{current_user.language}.html", current_user=current_user)  # type: ignore


@app.route('/lesson_for_topic/<language>/<topic>')
def lesson_for_topic(language, topic):
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    return render_template(f"lessons/{language}/{topic}.html", current_user=current_user)


@app.route('/conjugation_drill_tenses')  # type: ignore
def conjugation_drill_tenses():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    return render_template(f"conjugation_drill_tenses_{current_user.language}.html", current_user=current_user)  # type: ignore


@app.route('/conjugation_drill_for_tense/<tense>')  # type: ignore
def conjugation_drill_for_tense(tense):
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    return render_template(f"conjugation_drill_for_tense_{current_user.language}.html", tense=tense, current_user=current_user)  # type: ignore


@app.route('/conjugation_drill_for_verb/<tense>/<verb>', methods=["GET", "POST"])
def conjugation_drill_for_verb(tense, verb):
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    # def set_random_verb():
        # random_verb = pd.read_csv(f"static/data/{current_user.language}/verbs/{verb}.csv").sample() # type: ignore

        # session["pronoun"] = random_verb["pronoun"].values[0]
        # session["conjugated_verb"] = random_verb[tense].values[0]
        # session["verb_id"] = random_verb["verb_id"].values[0]
        # session["verb"] = verb
    def set_random_verb():
        words = pd.read_csv(f"static/data/{current_user.language}/verbs/{verb}.csv")  # type: ignore
        words = words.values.tolist()

        random_sentence = random.choice(words)

        session["pronoun"] = random_sentence[0]
        index = 0
        if current_user.language == "italian":  # type: ignore
            if tense == "presente":
                index = 1
            elif tense == "futuro_semplice":
                index = 2
        elif current_user.language == "german":  # type: ignore
            if tense == "praesens":
                index = 1
            elif tense == "praeteritum":
                index = 2
            elif tense == "perfekt":
                index = 3
            elif tense == "plusquamperfekt":
                index = 4
            elif tense == "futur_eins":
                index = 5
            elif tense == "futur_zwei":
                index = 6
        elif current_user.language == "spanish":  # type: ignore
            if tense == "presente":
                index = 1
            elif tense == "futuro":
                index = 2


        session["conjugated_verb"] = random_sentence[index]
        session["verb_id"] = random_sentence[len(random_sentence) - 1]
        session["verb"] = verb

    if current_user.language == "italian":  # type: ignore
        if not tense in ["presente", "futuro_semplice"]:
            flash("Unknown tense: " + tense)
            return redirect("/conjugation_drill_tenses")

        if not verb in verbs_italian:
            flash("Unknown verb: " + verb)
            return redirect("/conjugation_drill_tenses")
    elif current_user.language == "german":  # type: ignore
        if not verb in verbs_german:
            flash("Unknown verb: " + verb)
            return redirect("/conjugation_drill_tenses")
    elif current_user.language == "spanish":  # type: ignore
        if not verb in verbs_spanish:
            flash("Unknown verb: " + verb)
            return redirect("/conjugation_drill_tenses")

    if request.form.get("user_input") != None:
        user_input = unidecode(request.form.get("user_input")).lower()  # type: ignore
        verb_is_correct = user_input == unidecode(session["conjugated_verb"]).lower()

        if differ_by_single_char(user_input, unidecode(session["conjugated_verb"])):
            flash("You missed one letter.")
            return render_template(
                'conjugation_drill_for_verb.html',
                tense=tense,
                verb_is_correct=verb_is_correct,
                user_input=user_input,
                current_user=current_user,
                play_audio=True,
                language=current_user.language,  # type: ignore
            )
        return render_template(
            'conjugation_drill_for_verb.html',
            tense=tense,
            verb_is_correct=verb_is_correct,
            current_user=current_user,
            play_audio=True,
            language=current_user.language,  # type: ignore
        )

    set_random_verb()
    return render_template(
        'conjugation_drill_for_verb.html',
        tense=tense,
        current_user=current_user,
        language=current_user.language,  # type: ignore
    )

@app.route('/vocabulary_for_topic/<topic>', methods=["GET", "POST"])
def vocabulary_for_topic(topic):
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    def set_random_word():  # Setting a random word to the session
        words = pd.read_csv(f"static/data/{current_user.language}/vocabulary/{topic}.csv")  # type: ignore
        words = words.values.tolist()

        random_word = random.choice(words)

        session["italian"] = random_word[0]
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
            unidecode(session["italian"]).lower() or
            user_input in unidecode(session["italian"]).lower().split("||")
        )

        if differ_by_single_char(user_input, unidecode(session["italian"])):
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


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.form.get("submit"):
        # Getting the data and storing it in variables
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        language = request.form.get("language")

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
            ),
            language=language
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
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
            login_user(user, remember=True)
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


@app.route('/delete_profile', methods=["GET", "POST"])
def delete_profile():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    db.session.delete(current_user)
    db.session.commit()
    return redirect(url_for("index"))


@app.route('/change_password', methods=["GET", "POST"])  # type: ignore
def change_password():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    if request.form.get("submit"):
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        if not check_password_hash(current_user.password, old_password):  # type: ignore
            flash("Old password is incorrect!")
            return redirect(url_for("profile"))
        if not has_only_allowed_symbols(new_password):
            flash("You used not allowed symbols!")
            return redirect(url_for("profile"))
        current_user.password = generate_password_hash(
            new_password,  # type: ignore
            method='pbkdf2:sha256',
            salt_length=8
        )
        db.session.commit()
        flash("Password changed!")
        return redirect(url_for("profile"))
    flash("Password not changed!")
    return redirect(url_for("profile"))

@app.route('/change_username', methods=["GET", "POST"])  # type: ignore
def change_username():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    if request.form.get("submit"):
        new_username = request.form.get("new_username")
        if not has_only_allowed_symbols(new_username):
            flash("You used not allowed symbols!")
            return redirect(url_for("profile"))
        current_user.username = new_username
        db.session.commit()
        flash("Username changed!")
        return redirect(url_for("profile"))
    flash("Username not changed!")
    return redirect(url_for("profile"))
    

@app.route('/change_language', methods=["GET", "POST"])  # type: ignore
def change_language():
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for("index"))
    if request.form.get("submit"):
        new_language = request.form.get("new_language")
        current_user.language = new_language
        db.session.commit()
        flash("Language changed!")
        return redirect(url_for("profile"))
    flash("Language not changed!")
    return redirect(url_for("profile"))
    


@app.errorhandler(404)
def error_404(e):
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
    app.run(host='127.0.0.1', port=8000, debug=True)
