from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired


class AskQuestionForm(FlaskForm):
    body = TextAreaField('Ваш вопрос', validators=[DataRequired()])
    attachment = FileField('Прикрепить скриншот (необязательно)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Только изображения и PDF.')
    ])
    submit = SubmitField('Отправить вопрос')


class AnswerForm(FlaskForm):
    body = TextAreaField('Ваш ответ', validators=[DataRequired()])
    submit = SubmitField('Отправить ответ')


class MentorCourseSelectionForm(FlaskForm):
    courses = SelectMultipleField('Выберите курсы', validators=[])
    submit = SubmitField('Сохранить')
