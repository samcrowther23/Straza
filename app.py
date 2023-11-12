from flask import Flask
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    jsonify,
    make_response,
)
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from wtforms import StringField, SubmitField, PasswordField, validators
from flask_session import Session
import secrets
from sqlalchemy import create_engine
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    Float,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import os
import json
from datetime import date, timedelta
import math


# config app
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)


# Set up URI
username = "root"
password = "password"
host = "localhost"
database_name = "users"
mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}/{database_name}"
app.config["SQLALCHEMY_DATABASE_URI"] = mysql_uri

db = SQLAlchemy(app)
migrate = Migrate(app, db)


Base = db.Model

empty_row = [0, 0, 0, 0, 0, 0, 0, 0]
default_table = json.dumps([empty_row])
class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    distance = Column(Float)
    run_type = Column(String(50))
    zone_2_time = Column(Integer)
    zone_3_time = Column(Integer)
    zone_4_time = Column(Integer)
    zone_5_time = Column(Integer)
    total_time = Column(Integer)
    text = Column(String(200))

    user_id = Column(
        Integer, ForeignKey("user.id")
    )  # Add this line to define the foreign key
    user = relationship("User", back_populates="runs")

    def __repr__(self):
        return f"id={self.id}, type={self.run_type}, date={self.date}, distance={self.distance})"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(100))
    profile_picture_path = Column(String(100), default="default_profile_picture.jpg")
    table_data = Column(JSON, default=default_table)
    table_colour = Column(JSON, default=default_table)
    run_matrix = Column(JSON, default=json.dumps([]))
    runs_by_week_matrix = Column(JSON, default=json.dumps([]))
    totalDistance_matrix = Column(JSON, default=json.dumps([]))

    runs = relationship(
        "Run", back_populates="user"
    )  # Add a relationship to the Run class

    def __repr__(self):
        runs_info = ", ".join(
            [
                f"Run(id={run.id}, date={run.date}, distance={run.distance})"
                for run in self.runs
            ]
        )
        return f"<User(id={self.id}, username={self.username}, runs=[{runs_info}])>"

    def clear_run_data(self):
        try:
            db_session.query(Run).filter(Run.user_id == self.id).delete()
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    def update_matrix(self):
        try:
            sorted_runs = sorted(self.runs, key=lambda run: run.date)
            if not sorted_runs:
                    self.run_matrix = []
                    self.totalDistance_matrix = []
                    return None
            start_date = sorted_runs[0].date
            end_date = sorted_runs[-1].date
            first_monday = start_date - timedelta(days=start_date.weekday())
            number_of_days = (end_date - first_monday).days + 1
            number_of_weeks = math.ceil(number_of_days / 7)


            self.run_matrix = [[0] * 7 for _ in range(number_of_weeks)]
            self.totalDistance_matrix = [0.0 for _ in range(number_of_weeks)]
            self.runs_by_week_matrix = [[] for _ in range(number_of_weeks)]

            

            for run in sorted_runs:
                date = run.date
                days_since_first = (date - first_monday).days
                row = days_since_first // 7
                column = date.weekday()
                self.run_matrix[row][column] += 1
                self.totalDistance_matrix[row] += run.distance
                self.runs_by_week_matrix[row].append(run.id)

            # Serialize the matrices
            self.run_matrix = json.dumps(self.run_matrix)
            self.totalDistance_matrix = json.dumps(self.totalDistance_matrix)
            self.runs_by_week_matrix = json.dumps(self.runs_by_week_matrix)

            db_session.commit()

        except Exception as e:
            print(f"Error: {e}")
            db_session.rollback()
            raise e
        finally:
            db_session.close()


class LogInForm(FlaskForm):
    username = StringField(
        "username", validators=[validators.DataRequired(message="Username required")]
    )
    password = PasswordField(
        "Password",
        validators=[
            validators.DataRequired(message="Password required"),
            validators.EqualTo("password", message="Incorrect Password"),
        ],
    )

    submit = SubmitField("Sign Up")


class SignUpForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            validators.DataRequired(message="Username required"),
            validators.Length(4, 25),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            validators.DataRequired(message="Password required"),
            validators.EqualTo("confirm_password", message="Passwords must match"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            validators.DataRequired(message="Comfirmation password required"),
        ],
    )
    submit = SubmitField("Sign Up")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(
        "Old Password",
        validators=[
            validators.DataRequired(message="Password required"),
        ],
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            validators.DataRequired(message="Password required"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            validators.DataRequired(message="password required"),
            validators.EqualTo("new_password", message="Passwords must match"),
        ],
    )


def get_user():
    user_id = session.get("user_id")
    user = db_session.query(User).get(user_id)
    if user:
        return user
    else:
        return None


def get_profile_picture_path(user):
    if user.profile_picture_path:
        return user.profile_picture_path
    else:
        return "default_profile_picture.jpg"


# index
@app.route("/", methods=["GET", "POST"])
def index():
    button_id = request.form.get("button_id")

    if button_id == "login":
        return redirect(url_for("login"))
    elif button_id == "signup":
        return redirect(url_for("signup"))

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LogInForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = db_session.query(User).filter(User.username == username).first()

        if user and user.password is not None and password is not None:
            if user.password == password:  # type: ignore
                flash(f"Logged in as {username}")
                session["logged_in"] = True
                session["user_id"] = user.id
                return redirect(url_for("home"))
        else:
            flash("Invalid username or password")

    return render_template("login.html", form=form)


# Sign up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        # Handle form submission
        username = form.username.data
        username_taken = db_session.query(User).filter_by(username=username).first()
        if not username_taken:
            password = form.password.data
            new_user = User(username=username, password=password) #type: ignore
            db_session.add(new_user)
            db_session.commit()
            session["logged_in"] = True
            session["user_id"] = new_user.id
            flash(f"Hi {username}, welcome to Straza")
            return redirect(url_for("home"))
        else:
            flash("username_taken")

    return render_template("signup.html", form=form)


@app.route("/home")
def home():
    return render_template("home.html")


column_names = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "Total",
]


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = get_user()

    if user:
        table_data_json = user.table_data
        table_data = json.loads(table_data_json)

        profile_picture_path = get_profile_picture_path(user)
        if request.form:
            button = request.form.get("action")

            if button == "edit":
                return redirect(url_for("settings"))
            elif button == "stats":
                return redirect(url_for("runs"))
            elif button == "add_run":
                return redirect(url_for("log_run"))
            elif button == "add_workout":
                return redirect(url_for("log_workout"))

        return render_template(
            "profile.html",
            username=user.username,
            profile_picture_path=profile_picture_path,
            column_names=column_names,
            table_data=table_data,
        )
    else:
        return redirect(url_for("logout"))


@app.route("/runs")
def runs():
    user = get_user()

    if user:
        sorted_runs = []  # Initialize sorted_runs with an empty list
        empty_text = None

        if db_session.query(Run).filter(Run.user_id == user.id).count() > 0:
            if user.runs:
                sorted_runs = sorted(user.runs, key=lambda run: run.date)

        else:
            empty_text = "Bit empty round here... Go on a run"

        return render_template(
            "runs.html",
            matrix=json.loads(user.run_matrix),
            totalDistance=json.loads(user.totalDistance_matrix),
            runs=sorted_runs,
            empty_text=empty_text,
        )

    return redirect(url_for("index"))


@app.route("/run_details/<int:run_id>")
def run_details(run_id):
    run = db_session.query(Run).filter(Run.id == run_id).first()
    #print(run)
    time_in_zones = [0, 0, 0, 0]
    formatted_date = "1/1/70"

    if run is not None:
        z2, z3, z4, z5 = (
            run.zone_2_time,
            run.zone_3_time,
            run.zone_4_time,
            run.zone_5_time,
        )
        #total = run.total_time

        # try:
        #     z1 = float(total - z2 - z3 - z4 - z5)  # type: ignore
        # except Exception as e:
        #     flash(f"An error has occurred: {e}")
        #     z1 = 0

        # if z1 < 0:
        #     total = z2 + z3 + z4 + z5
        #     z1 = 0

        time_in_zones = [z2, z3, z4, z5]
        formatted_date = run.date.strftime("%d/%m/%y")

    return render_template(
        "run_details.html",
        run=run,
        time_in_zones=time_in_zones,
        formatted_date=formatted_date,
    )


@app.route("/run_details/<int:run_id>/delete")
def delete_run(run_id):
    try:
        distance = None
        user = get_user()
        if user:
            run = db_session.query(Run).filter_by(id=run_id).first()

            if run:
                distance = run.distance
                db_session.delete(run)
                db_session.commit()
                                 
                user.update_matrix()
                if distance == 0.0: #type: ignore
                    flash("workout deleted")
                else:
                    flash("run deleted") 

    except:
        flash("run doesnt exist")

    return redirect(url_for("runs"))




@app.route("/week_details/<int:week>")
def week_details(week):
    user = get_user()
    time_in_zones = [0, 0, 0, 0]
    total_time = 0
    if user:
        run_ids = json.loads(user.runs_by_week_matrix)[week]
        for run_id in run_ids:
            run = db_session.query(Run).filter_by(id=run_id).first()
            if run:
                time_in_zones[0] += int(run.zone_2_time) #type:ignore
                time_in_zones[1] += int(run.zone_3_time) #type:ignore
                time_in_zones[2] += int(run.zone_4_time) #type:ignore
                time_in_zones[3] += int(run.zone_5_time) #type:ignore
                total_time += run.total_time
        return render_template("week_details.html", time_in_zones=time_in_zones, week=week, total_time=total_time)

                
    return(redirect(url_for("index")))

def get_form_value_as_int(field_name):
    value = request.form.get(field_name)
    if value is not None:
        try:
            #print(f"converting {field_name}")
            return int(value)
        except ValueError:
            #print(f"could not convert {field_name} to int")
            return int(0)
    return None

def get_form_value_as_float(field_name):
    value = request.form.get(field_name)
    if value is not None:
        try:
            #print(f"converting {field_name}")
            return float(value)
            
        except ValueError:
            #print(f"could not convert {field_name} to float")
            return float(0.0)
    return None


@app.route("/log_run", methods=["POST", "GET"])
def log_run():
    if request.form:
        date_str = request.form.get("date")
        if date_str:
            year, month, day = date_str.split("-")
            run_date = date(int(year), int(month), int(day))
        else:
            run_date = date(1970, 1, 1)

        distance = get_form_value_as_float("distance")
        run_type = request.form.get("run_type")
        zone_2_time = get_form_value_as_int("zone_2_time")
        zone_3_time = get_form_value_as_int("zone_3_time")
        zone_4_time = get_form_value_as_int("zone_4_time")
        zone_5_time = get_form_value_as_int("zone_5_time")
        total_time = get_form_value_as_int("total_time")
        text = request.form.get("additional_notes")

        # Create a new Run object
        new_run = Run(
            date=run_date,
            distance=distance,
            run_type=run_type,
            zone_2_time=zone_2_time,
            zone_3_time=zone_3_time,
            zone_4_time=zone_4_time,
            zone_5_time=zone_5_time,
            total_time=total_time,
            text=text,
        ) #type: ignore

        # Associate the run with the logged-in user
        user = get_user()
        if user:
            user.runs.append(new_run)
            db_session.commit()
            user.update_matrix()
            flash("Run logged successfully")
        else:
            flash("No user")

        return redirect(url_for("profile"))

    return render_template("log_run.html")

@app.route("/log_workout", methods=["POST", "GET"])
def log_workout():
    if request.form:
        date_str = request.form.get("date")
        if date_str:
            year, month, day = date_str.split("-")
            run_date = date(int(year), int(month), int(day))
        else:
            run_date = date(1970, 1, 1)

        workout = request.form.get("workout")
        zone_2_time = get_form_value_as_int("zone_2_time")
        zone_3_time = get_form_value_as_int("zone_3_time")
        zone_4_time = get_form_value_as_int("zone_4_time")
        zone_5_time = get_form_value_as_int("zone_5_time")
        total_time = get_form_value_as_int("total_time")
        text = request.form.get("additional_notes")
        

        new_workout = Run(
        date=run_date,
        distance=0,
        run_type=workout,
        zone_2_time=zone_2_time,
        zone_3_time=zone_3_time,
        zone_4_time=zone_4_time,
        zone_5_time=zone_5_time,
        total_time=total_time,
        text=text,
        ) #type: ignore

        user = get_user()
        if user:
            user.runs.append(new_workout)
            db_session.commit()
            user.update_matrix()
            flash("Run logged successfully")
        else:
            flash("No user")

        return redirect(url_for("profile"))

    return render_template("log_workout.html")

@app.route("/edit_run/<int:run_id>", methods=["GET", "POST"])
def edit_run(run_id):
    run = db_session.query(Run).filter(Run.id == run_id).first()
    if run:
        if request.form:
            date_str = request.form.get("date")
            if date_str:
                year, month, day = date_str.split("-")
                run_date = date(int(year), int(month), int(day))
            else:
                run_date = date(1970, 1, 1)

            distance = get_form_value_as_float("distance")
            run_type = request.form.get("run_type")
            zone_2_time = get_form_value_as_int("zone_2_time")
            zone_3_time = get_form_value_as_int("zone_3_time")
            zone_4_time = get_form_value_as_int("zone_4_time")
            zone_5_time = get_form_value_as_int("zone_5_time")
            total_time = get_form_value_as_int("total_time")
            text = request.form.get("additional_notes")

            # Create a new Run object
            edited_run = Run(
                date=run_date,
                distance=distance,
                run_type=run_type,
                zone_2_time=zone_2_time,
                zone_3_time=zone_3_time,
                zone_4_time=zone_4_time,
                zone_5_time=zone_5_time,
                total_time=total_time,
                text=text,
            ) #type: ignore

            # Associate the run with the logged-in user
            user = get_user()
            if user:
                db_session.query(Run).filter(Run.id == run_id).delete()
                user.runs.append(edited_run)
                db_session.commit()
                edited_run_id = edited_run.id
                flash("Run editted")
                return redirect(url_for("run_details", run_id=edited_run_id))
            else:
                flash("No user")
                return redirect(url_for("index"))
        return render_template("edit_run.html", run=run)
    return redirect(url_for("index"))


@app.route("/update_table", methods=["POST"])
def update_table():
    user = get_user()
    if user:
        table_data = json.loads(user.table_data)
        if request.is_json:
            data = request.get_json()
            edited_data = data.get("edited_data")
            button = data.get("action")
            if edited_data:
                row_index, col_index, value = json.loads(edited_data)

                row_index = int(row_index) - 1
                col_index = int(col_index)
                try:
                    value = float(value)
                except ValueError:
                    value = 0

                table_data[row_index][col_index] = value

                # update row total
                row = table_data[row_index]
                row_sum = sum(row[:-1])
                row[-1] = row_sum
                table_data[row_index] = row

                # save table
                user.table_data = json.dumps(table_data)
                db_session.commit()
                return jsonify({"table_data": table_data})

            elif button in ["add_row", "clear_empty_rows"]:
                if button == "add_row":
                    table_data.append(empty_row)
                    user.table_data = json.dumps(table_data)
                    db_session.commit()
                    return jsonify({"table_data": table_data})

                if button == "clear_empty_rows":
                    cleared_table_data = [row for row in table_data if row != empty_row]
                    user.table_data = json.dumps(cleared_table_data)
                    db_session.commit()
                    return jsonify({"table_data": cleared_table_data})

            else:
                return jsonify({"error": "Invalid Content-Type"})
    return jsonify({"error": "something went wrong"})


@app.route("/settings", methods=["GET", "POST"])
def settings():
    action = request.form.get("action")
    if action:
        user = get_user()
        if user:
            if action == "profilePicture":
                return redirect(url_for("upload_profile_picture"))
            elif action == "changePassword":
                return redirect(url_for("change_password"))
            elif action == "resetRuns":
                db_session.query(Run).filter(Run.user_id == user.id).delete()
                db_session.commit()
                flash("Runs reset")
            else:
                flash("invalid action")
        else:
            flash("user not found")
        return redirect(url_for("profile"))
    return render_template("settings.html")


@app.route("/settings/uploadprofilepicture", methods=["GET", "POST"])
def upload_profile_picture():
    if request.method == "POST":
        uploaded_file = request.files.get("file")  # Use .get() for safer access
        if uploaded_file:
            user_id = session.get("user_id")
            user = db_session.query(User).get(user_id)
            if user:
                new_file_name = f"{user_id}_profilepicture.jpg"
                user.profile_picture_path = new_file_name
                save_path = os.path.join("static", "profile_pictures", new_file_name)
                # Make sure directories exist
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                uploaded_file.save(save_path)
                db_session.commit()
                flash("Profile picture uploaded successfully!", "success")
                return redirect(url_for("profile"))
            else:
                flash("Failed to upload profile picture", "error")

    return render_template("upload_profile_picture.html")


@app.route("/settings/change_password", methods=["GET", "POST"])
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Handle form submission
        old_password = form.old_password.data

        user = get_user()
        if user and user.password == old_password:
            new_password = form.new_password.data
            user.password = new_password
            flash("password changed successfully", "success")
            return redirect(url_for("profile"))
        else:
            flash("old password incorrect")
    return render_template("change_password.html", form=form)


@app.route("/users")
def users():
    users = db_session.query(User).all()

    return render_template("users.html", users=users)


@app.route("/users/action", methods=["POST", "GET"])
def user_action():
    user_id = request.form.get("user_id")
    action = request.form.get("action")
    if user_id and action:
        user = db_session.query(User).get(user_id)
        if user:
            if action == "delete":
                db_session.delete(user)
                db_session.commit()
                flash(f"user {user.username} deleted")
            elif action == "resetTable":
                user.table_data = default_table
                db_session.commit()
                flash(f"user {user.username}'s table reset")
            elif action == "resetRuns":
                db_session.query(Run).filter(Run.user_id == user_id).delete()
                db_session.commit()
                # user.clear_run_data()
                flash(f"{user.username} run data reset")
            else:
                flash("Invalid action")
        else:
            flash("user not found")
    return redirect(url_for("users"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for("index"))


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    error_message = e.description if e.description else "An error occurred."
    return (
        render_template("error.html", error_code=e.code, error_message=error_message),
        e.code,
    )


if __name__ == '__main__':
    with app.app_context():
        Session = sessionmaker(bind=db.engine)
        db_session = Session()
        db.create_all()
        app.run(debug=True)