from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, Email


class CourseForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ('Программирование', 'Программирование'),
        ('Математика', 'Математика'),
        ('Наука', 'Наука'),
        ('Дизайн', 'Дизайн'),
        ('Бизнес', 'Бизнес'),
        ('Языки', 'Языки'),
        ('Другое', 'Другое')
    ])
    level = SelectField('Уровень', choices=[
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый')
    ])
    thumbnail = FileField('Обложка', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения!')
    ])
    is_published = BooleanField('Опубликовано')
    submit = SubmitField('Сохранить')


class LessonForm(FlaskForm):
    course = SelectField('Курс', validators=[DataRequired()], coerce=int)
    title = StringField('Название', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание', validators=[Optional()])
    video = FileField('Видео', validators=[
        FileAllowed(['mp4', 'webm'], 'Только видео файлы (mp4, webm)!')
    ])
    duration = IntegerField('Длительность (секунд)', validators=[Optional()])
    order_index = IntegerField('Порядок', default=0)
    is_published = BooleanField('Опубликовано')
    submit = SubmitField('Сохранить')


class UserCreateForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Роль', choices=[('student', 'Студент'), ('admin', 'Администратор'), ('mentor', 'Ментор'), ('parent', 'Родитель')])
    is_active = BooleanField('Активен', default=True)
    submit = SubmitField('Сохранить')


class UserEditForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Роль', choices=[('student', 'Студент'), ('admin', 'Администратор'), ('mentor', 'Ментор'), ('parent', 'Родитель')])
    is_active = BooleanField('Активен')
    new_password = PasswordField('Новый пароль', validators=[Optional(), Length(min=6)])
    submit = SubmitField('Сохранить')


class EnrollmentForm(FlaskForm):
    user = SelectField('Пользователь', validators=[DataRequired()], coerce=int)
    course = SelectField('Курс', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        self.current_enrollment_id = kwargs.pop('current_enrollment_id', None)
        super().__init__(*args, **kwargs)
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        from app.models import Enrollment
        existing = Enrollment.query.filter_by(
            user_id=self.user.data,
            course_id=self.course.data
        ).first()
        if existing and existing.id != self.current_enrollment_id:
            self.user.errors.append('Этот пользователь уже записан на этот курс!')
            return False
        return True
