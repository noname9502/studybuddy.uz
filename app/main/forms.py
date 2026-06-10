from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class CommentForm(FlaskForm):
    body = TextAreaField('Комментарий', validators=[DataRequired()])
    submit = SubmitField('Опубликовать')


class RatingForm(FlaskForm):
    score = IntegerField('Оценка', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Оценить')
