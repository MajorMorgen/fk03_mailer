from flask import Flask, render_template
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, SelectField, widgets, SelectMultipleField
from wtforms.validators import InputRequired, Email, Length, AnyOf
from flask_bootstrap import Bootstrap
import os.path
import csv
from datetime import datetime
import pytz
from secrets import flask_key
import subprocess

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = flask_key
app.config['TESTING'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

STUDIES=[
    ("FAB", "Fahrzeugtechnik Bachelor"),
    ("LRB", "Luft- und Raumfahrttechnik Bachelor"),
    ("MBB", "Maschinenbau Bachelor"),
    ("FAM", "Fahrzeugtechnik Master"),
    ("LRM", "Luft- und Raumfahrttechnik Master"),
    ("MBM", "Maschinenbau Master"),
    ("FEM", "Fahrzeugmechatronik"),
    ("TBM", "Technische Berechnung und Simulation"),
    ("RSM", "Applied Research in Engineering Sciences"),
]


def current_path():
        dir_path = os.path.dirname(os.path.realpath(__file__)) + "/"
        return str(dir_path)    

def read_in_csv() -> list:

        csv_list = []
        with open(MAIL_FILENAME, newline="") as file:
            reader = csv.reader(file, delimiter=";")
            for row in reader:
                csv_list.append(row)
        return csv_list


def registered():
    check_for_csv()
    return len(read_in_csv())

def check_for_csv():
        if not os.path.isfile(MAIL_FILENAME):
            with open(MAIL_FILENAME, "w") as _:
                pass


MAIL_FILENAME = current_path() + "data/registered.csv"
BACKUP_FILENAME = current_path() + "data/backup.csv"

class DataHandler:


    def __init__(self, data):

        self.email = data["email"]
        self.stud = data["stud"]

        self.answer = dict(
            mode="default",
            email=self.email,
            stud=self.stud,
        )


    def mail_exists(self):
        csv_list = read_in_csv()
        mail_studs = [(i[0], i[1]) for i in csv_list]
        if (self.email, self.stud) in mail_studs:
            self.answer["mode"] = "already_exists"
            return True
        else:
            return False


    def add_mail_to_csv(self):

        for filename in [MAIL_FILENAME, BACKUP_FILENAME]:

            now = datetime.now(pytz.timezone('Europe/Amsterdam'))
            date_time = now.strftime("%d.%m.%Y_%H:%M:%S")

            with open(filename, "a", newline="") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow([self.email, self.stud, date_time])
                file.close()

        self.answer["mode"] = "add_success"


    def handle(self):
        check_for_csv()
        if not self.mail_exists():
            self.add_mail_to_csv()
       


class MailRemover:

    def __init__(self, data):

        self.email = data["email"]

        self.answer = dict(
            mode="default",
            email=self.email
        )


    
    def check_for_csv(self):
        if not os.path.isfile(MAIL_FILENAME):
            with open(MAIL_FILENAME, "w") as _:
                pass


    def mail_exists(self, all_mails_studs):

        mails = [i[0] for i in all_mails_studs]

        if self.email in mails:
            return True
        else:
            self.answer["mode"] = "not_found"
            return False


    def remove_mails(self, all_mails_studs):
        remove_counter = 0
        updated_mails = []
        for entry in all_mails_studs:
            if entry[0] != self.email:
                updated_mails.append(entry)
            else:
                remove_counter += 1

        self.answer["remove_counter"] = remove_counter
        self.write_new_csv(updated_mails)


    def write_new_csv(self, updated_mails):

        with open(MAIL_FILENAME, "w", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerows(updated_mails)
            file.close()
            self.answer["mode"] = "remove_success"


    def remove(self):
        check_for_csv()
        all_mails_studs = read_in_csv()
        if self.mail_exists(all_mails_studs):
            self.remove_mails(all_mails_studs)



class LoginForm(FlaskForm):
    username = StringField('Deine E-mail', render_kw={"placeholder": "deinemail@example.de"}, validators=[InputRequired(), Email(message='Bitte gib eine gültige E-mail ein.'), Length(max=50)])
    group = SelectField(label='Dein Studiengang', choices=STUDIES)
  

class RemoveForm(FlaskForm):
    mail_to_remove = StringField('Deine E-mail', render_kw={"placeholder": "deinemail@example.de"}, validators=[InputRequired(), Email(message='Bitte gib eine gültige E-mail ein.'), Length(max=50)])



@app.route('/', methods=['GET', 'POST'])
def register():
    already_registered = registered()
    form = LoginForm()
    if form.validate_on_submit():

        form_data = dict(
            email=form.username.data,
            stud=form.group.data
        )
        
        handler = DataHandler(form_data)
        handler.handle()
        
        
        return render_template('index.html', form=form, answer=handler.answer, mode="register", counter=already_registered)

    return render_template('index.html', form=form, answer=None, mode="register", counter=already_registered)



@app.route('/remove', methods=['GET', 'POST'])
def delete():

    already_registered = registered()
    form = RemoveForm()
    if form.validate_on_submit():

        form_data = dict(
            email=form.mail_to_remove.data,
            stud="EGAL"
        )
        
        remover = MailRemover(form_data)
        remover.remove()
        
        
        return render_template('index.html', form=form, answer=remover.answer, mode="remove", counter=already_registered)

    return render_template('index.html', form=form, answer=None, mode="remove", counter=already_registered)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, ssl_context='adhoc')