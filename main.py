import random
from functools import wraps
import os
import functions
import pandas as pd
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_compress import Compress
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from unidecode import unidecode
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import SocketIO

# ! Remember to add the module to the requirements.txt file


app = Flask(__name__)
socket = SocketIO(app)
Compress(app)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
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
        if current_user.username != "admin":
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.template_filter('decode')
def decode(string_to_decode):
    return unidecode(string_to_decode)


@app.template_filter('format')
def format(string_to_format):
    return string_to_format.replace("_", " ").capitalize()


topics = [
    "foods", "drinks", "fruits",
    "transport"
]

verbs_italian = [
    "abitare", "andare", "avere",
    "capire", "dare", "dire",
    "dormire", "dovere", "essere",
    "fare", "finire", "leggere",
    "parlare", "potere", "sapere",
    "stare", "trovare", "uscire",
    "vedere", "venire", "volere"
]
verbs_german = [
    "sein", "haben"
]
verbs_spanish = [
    "ser", "estar", "haber"
]

italian_tenses = ["presente", "futuro_semplice"]
german_tenses = ["praesens", "praeteritum", "perfekt", "plusquamperfekt", "futur_eins", "futur_zwei"]
spanish_tenses = ["presente", "futuro"]
italian_tenses_formatted = ["Presente", "Futuro semplice"]
german_tenses_formatted = ["Präsens", "Präteritum", "Perfekt", "Plusquamperfekt", "Futur I", "Futur II"]
spanish_tenses_formatted = ["Presente", "Futuro"]

italian_lessons = ["the_alphabet"]
german_lessons = ["the_alphabet"]
spanish_lessons = ["the_alphabet"]


@app.route('/')  
def index():
    if current_user.is_authenticated:  
        if current_user.language == "italian":  
            return render_template(
            'index.html',
            current_user=current_user,
            topics=topics,
            tenses=["Presente", "Futuro Semplice"],
            lessons_list=italian_lessons,
        )
        elif current_user.language == "german":  
            return render_template(
            'index.html',
            current_user=current_user,
            topics=topics,
            tenses=["Präsens", "Präteritum", "Perfekt", "Plusquamperfekt", "Futur I", "Futur II"],
            lessons_list=german_lessons,
        )
        elif current_user.language == "spanish":  
            return render_template(
            'index.html',
            current_user=current_user,
            topics=topics,
            tenses=["Presente", "Futuro"],
            lessons_list=spanish_lessons,
        )
    else:
        return render_template(
        'index.html',
        current_user=current_user,
    )


@app.route('/vocabulary_topics')
def vocabulary_topics():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    return render_template("vocabulary_topics.html", current_user=current_user)


@app.route('/lessons')  
def lessons():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    if current_user.language == "italian":  
        return render_template(
            "lessons.html",
            lessons=italian_lessons,
            current_user=current_user
        ) 
    if current_user.language == "spanish":  
        return render_template(
            "lessons.html",
            lessons=spanish_lessons,
            current_user=current_user
        ) 
    if current_user.language == "german":  
        return render_template(
            "lessons.html",
            lessons=german_lessons,
            current_user=current_user
        )


@app.route('/lesson_for_topic/<topic>')
def lesson_for_topic(topic):
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    return render_template(f"lessons/{current_user.language}/{topic}.html", current_user=current_user)  


@app.route('/conjugation_drill_tenses')  
def conjugation_drill_tenses():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    if current_user.language == "italian": 
        return render_template(
            "conjugation_drill_tenses.html",
            tenses_formatted=italian_tenses_formatted,
            tenses=italian_tenses,
            current_user=current_user
        )
    if current_user.language == "german": 
        return render_template(
            "conjugation_drill_tenses.html",
            tenses_formatted=german_tenses_formatted,
            tenses=german_tenses,
            current_user=current_user
        )
    if current_user.language == "spanish": 
        return render_template(
            "conjugation_drill_tenses.html",
            tenses_formatted=spanish_tenses_formatted,
            tenses=spanish_tenses,
            current_user=current_user
        )


@app.route('/conjugation_drill_for_tense/<tense>')  
def conjugation_drill_for_tense(tense):
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    if current_user.language == "italian": 
        return render_template(
            "conjugation_drill_for_tense.html",
            verbs=verbs_italian,
            tense=tense,
            current_user=current_user
        )
    elif current_user.language == "german": 
        return render_template(
            "conjugation_drill_for_tense.html",
            verbs=verbs_german,
            tense=tense,
            current_user=current_user
        )
    elif current_user.language == "spanish": 
        return render_template(
            "conjugation_drill_for_tense.html",
            verbs=verbs_spanish,
            tense=tense,
            current_user=current_user
        )

@app.route('/conjugation_drill_for_verb/<tense>/<verb>', methods=["GET", "POST"])
def conjugation_drill_for_verb(tense, verb):
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    # def set_random_verb():
        # random_verb = pd.read_csv(f"static/data/{current_user.language}/verbs/{verb}.csv").sample()

        # session["pronoun"] = random_verb["pronoun"].values[0]
        # session["conjugated_verb"] = random_verb[tense].values[0]
        # session["verb_id"] = random_verb["verb_id"].values[0]
        # session["verb"] = verb
    def set_random_verb():
        words = pd.read_csv(f"static/data/{current_user.language}/verbs/{verb}.csv")
        words = words.values.tolist()

        random_sentence = random.choice(words)

        session["pronoun"] = random_sentence[0]
        index = 0
        if current_user.language == "italian":
            if tense == "presente":
                index = 1
            elif tense == "futuro_semplice":
                index = 2
        elif current_user.language == "german":
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
        elif current_user.language == "spanish":  
            if tense == "presente":
                index = 1
            elif tense == "futuro":
                index = 2


        session["conjugated_verb"] = random_sentence[index]
        session["verb_id"] = random_sentence[len(random_sentence) - 1]
        session["verb"] = verb

    if current_user.language == "italian":  
        if not tense in ["presente", "futuro_semplice"]:
            flash("Unknown tense: " + tense)
            return redirect("/conjugation_drill_tenses")

        if not verb in verbs_italian:
            flash("Unknown verb: " + verb)
            return redirect("/conjugation_drill_tenses")
    elif current_user.language == "german":  
        if not verb in verbs_german:
            flash("Unknown verb: " + verb)
            return redirect("/conjugation_drill_tenses")
    elif current_user.language == "spanish":  
        if not verb in verbs_spanish:
            flash("Unknown verb: " + verb)
            return redirect("/conjugation_drill_tenses")

    if request.form.get("user_input") != None:
        user_input = unidecode(request.form.get("user_input")).lower()  
        verb_is_correct = user_input == unidecode(session["conjugated_verb"]).lower()

        if functions.differ_by_single_char(user_input, unidecode(session["conjugated_verb"])):
            flash("You missed one letter.")
            return render_template(
                'conjugation_drill_for_verb.html',
                tense=tense,
                verb_is_correct=verb_is_correct,
                user_input=user_input,
                current_user=current_user,
                play_audio=True,
                language=current_user.language,  
            )
        return render_template(
            'conjugation_drill_for_verb.html',
            tense=tense,
            verb_is_correct=verb_is_correct,
            current_user=current_user,
            play_audio=True,
            language=current_user.language,  
        )

    set_random_verb()
    return render_template(
        'conjugation_drill_for_verb.html',
        tense=tense,
        current_user=current_user,
        language=current_user.language,  
    )

@app.route('/vocabulary_for_topic/<topic>', methods=["GET", "POST"])
def vocabulary_for_topic(topic):
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    def set_random_word():  # Setting a random word to the session
        words = pd.read_csv(f"static/data/{current_user.language}/vocabulary/{topic}.csv")  
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
            "user_input")).lower()  

        word_is_correct = user_input == (
            unidecode(session["italian"]).lower() or
            user_input in unidecode(session["italian"]).lower().split("||")
        )

        if functions.differ_by_single_char(user_input, unidecode(session["italian"])):
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

        if functions.empty(email, username, password):
            flash("Don't leave fields empty!")
            return redirect(url_for('register'))

        if not functions.has_only_allowed_symbols(username, password):
            flash("You used not allowed symbols!")
            return redirect(url_for('register'))

        if not functions.is_valid_email(email):
            flash("Please provide a valid email!")
            return redirect(url_for('register'))

        # Adding the user if the data is valid
        new_user = User(
            email=email,
            username=username,
            password=generate_password_hash(
                password,  
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



@app.route('/create_session_profile/<language>', methods=["GET", "POST"])  
def create_session_profile(language):
    session["language"] = language
    return redirect(url_for("index"))



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
        elif not check_password_hash(user.password, password):  
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user, remember=True)
            return redirect(url_for('index'))
    return render_template("login.html", current_user=current_user)


@app.route('/profile')
def profile():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    return render_template("profile.html", current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route('/delete_profile', methods=["GET", "POST"])
def delete_profile():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    db.session.delete(current_user)
    db.session.commit()
    return redirect(url_for("index"))


@app.route('/change_password', methods=["GET", "POST"])  
def change_password():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    if request.form.get("submit"):
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        if not check_password_hash(current_user.password, old_password):  
            flash("Old password is incorrect!")
            return redirect(url_for("profile"))
        if not functions.has_only_allowed_symbols(new_password):
            flash("You used not allowed symbols!")
            return redirect(url_for("profile"))
        current_user.password = generate_password_hash(
            new_password,  
            method='pbkdf2:sha256',
            salt_length=8
        )
        db.session.commit()
        flash("Password changed!")
        return redirect(url_for("profile"))
    flash("Password not changed!")
    return redirect(url_for("profile"))

@app.route('/change_username', methods=["GET", "POST"])  
def change_username():
    if not current_user.is_authenticated:  
        return redirect(url_for("index"))
    if request.form.get("submit"):
        new_username = request.form.get("new_username")
        if not functions.has_only_allowed_symbols(new_username):
            flash("You used not allowed symbols!")
            return redirect(url_for("profile"))
        current_user.username = new_username
        db.session.commit()
        flash("Username changed!")
        return redirect(url_for("profile"))
    flash("Username not changed!")
    return redirect(url_for("profile"))
    

@app.route('/change_language', methods=["GET", "POST"])  
def change_language():
    if not current_user.is_authenticated:  
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


socket.on('offline')
def offline():
    return app.send_static_file("offline.html")


@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')


@app.route('/robots.txt')
def robots_txt():
    return app.send_static_file('robots.txt')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
