from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Length

# Форма для регистрации пользователя
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('patient', 'Patient'), ('doctor', 'Doctor')], validators=[DataRequired()])
    submit = SubmitField('Register')

# Форма для логина
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Форма для записи на прием
class AppointmentForm(FlaskForm):
    patient_id = StringField('Patient ID', validators=[DataRequired()])
    doctor_id = StringField('Doctor ID', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Book Appointment')

# Форма для расписания врачей
class ScheduleForm(FlaskForm):
    doctor_id = StringField('Doctor ID', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Set Schedule')
