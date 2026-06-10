from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os
import uuid
from app.extensions import db
from app.models import User, Course, Lesson, Enrollment, Progress, Comment, Rating, Question, Answer
from app.main.forms import CommentForm, RatingForm
from app.mentor.forms import AskQuestionForm

main_bp = Blueprint('main', __name__)


def save_file(file, upload_folder):
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None


def get_course_avg_rating(course):
    total_score = 0
    count = 0
    for lesson in course.lessons:
        for rating in lesson.ratings:
            total_score += rating.score
            count += 1
    return round(total_score / count, 1) if count > 0 else 0


def get_lesson_avg_rating(lesson):
    if not lesson.ratings:
        return 0
    total = sum(r.score for r in lesson.ratings)
    return round(total / len(lesson.ratings), 1)


@main_bp.route('/')
def index():
    courses = Course.query.filter_by(is_published=True).order_by(Course.created_at.desc()).limit(6).all()
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    total_courses = Course.query.filter_by(is_published=True).count()
    total_students = User.query.filter_by(role='student').count()
    total_lessons = Lesson.query.filter_by(is_published=True).count()
    return render_template('index.html', courses=courses, courses_for_ai=all_courses, total_courses=total_courses,
                         total_students=total_students, total_lessons=total_lessons)


@main_bp.route('/courses')
def courses():
    query = Course.query.filter_by(is_published=True)
    category = request.args.get('category')
    level = request.args.get('level')
    search = request.args.get('search')

    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if search:
        query = query.filter(Course.title.ilike(f'%{search}%'))

    courses = query.all()
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    categories = ['Программирование', 'Математика', 'Наука', 'Дизайн', 'Бизнес', 'Языки', 'Другое']
    levels = ['beginner', 'intermediate', 'advanced']
    return render_template('courses.html', courses=courses, categories=categories, levels=levels,
                         selected_category=category, selected_level=level, search=search, courses_for_ai=all_courses)


@main_bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_published:
        flash('Курс не опубликован.', 'warning')
        return redirect(url_for('main.courses'))

    is_enrolled = False
    progress_data = {}
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        is_enrolled = enrollment is not None
        if is_enrolled:
            for lesson in course.lessons:
                progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
                progress_data[lesson.id] = progress.watched if progress else False

    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    avg_rating = get_course_avg_rating(course)
    return render_template('course_detail.html', course=course, is_enrolled=is_enrolled,
                         progress_data=progress_data, avg_rating=avg_rating, courses_for_ai=all_courses)


@main_bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_published:
        flash('Курс не опубликован.', 'warning')
        return redirect(url_for('main.courses'))

    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if existing:
        flash('Вы уже записаны на этот курс.', 'info')
    else:
        enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()
        flash('Вы успешно записались на курс!', 'success')
    return redirect(url_for('main.course_detail', course_id=course_id))


@main_bp.route('/lesson/<int:lesson_id>')
def lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if not course.is_published or not lesson.is_published:
        flash('Урок не доступен.', 'warning')
        return redirect(url_for('main.courses'))

    is_enrolled = False
    user_progress = None
    user_rating = None
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        is_enrolled = enrollment is not None
        if is_enrolled:
            user_progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
            user_rating = Rating.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()

    if not is_enrolled:
        flash('Пожалуйста, запишитесь на курс, чтобы просмотреть урок.', 'warning')
        return redirect(url_for('main.course_detail', course_id=course.id))

    comment_form = CommentForm()
    rating_form = RatingForm()
    ask_question_form = AskQuestionForm()
    
    # Get questions for this lesson
    questions = Question.query.filter_by(lesson_id=lesson.id).order_by(Question.created_at.desc()).all()

    prev_lesson = None
    next_lesson = None
    lessons = list(course.lessons)
    idx = next((i for i, l in enumerate(lessons) if l.id == lesson.id), -1)
    if idx > 0:
        prev_lesson = lessons[idx - 1]
    if idx < len(lessons) - 1:
        next_lesson = lessons[idx + 1]

    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    avg_rating = get_lesson_avg_rating(lesson)
    return render_template('lesson.html', lesson=lesson, course=course, comment_form=comment_form,
                         rating_form=rating_form, user_rating=user_rating, user_progress=user_progress,
                         prev_lesson=prev_lesson, next_lesson=next_lesson, avg_rating=avg_rating, courses_for_ai=all_courses,
                         ask_question_form=ask_question_form, questions=questions)


@main_bp.route('/lesson/<int:lesson_id>/comment', methods=['POST'])
@login_required
def post_comment(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(lesson_id=lesson.id, user_id=current_user.id, body=form.body.data)
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий опубликован!', 'success')
    return redirect(url_for('main.lesson', lesson_id=lesson_id))


@main_bp.route('/lesson/<int:lesson_id>/rate', methods=['POST'])
@login_required
def rate_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.get_json()
    score = data.get('score')
    if not score or score < 1 or score > 5:
        return jsonify({'success': False, 'error': 'Некорректная оценка'}), 400

    rating = Rating.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if rating:
        rating.score = score
    else:
        rating = Rating(user_id=current_user.id, lesson_id=lesson.id, score=score)
        db.session.add(rating)
    db.session.commit()
    return jsonify({'success': True, 'new_avg': get_lesson_avg_rating(lesson), 'total': len(lesson.ratings)})


@main_bp.route('/lesson/<int:lesson_id>/progress', methods=['POST'])
@login_required
def update_progress(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.get_json()
    watch_time = data.get('watch_time', 0)
    progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()

    if not progress:
        progress = Progress(user_id=current_user.id, lesson_id=lesson.id)
        db.session.add(progress)

    progress.watch_time = watch_time
    if data.get('watched') and not progress.watched:
        progress.watched = True
        progress.completed_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/profile')
@login_required
def profile():
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    courses_progress = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = len([l for l in course.lessons if l.is_published])
        watched_lessons = Progress.query.filter_by(user_id=current_user.id, watched=True).join(Lesson).filter(
            Lesson.course_id == course.id).count()
        progress_pct = int((watched_lessons / total_lessons) * 100) if total_lessons > 0 else 0
        courses_progress.append({'course': course, 'progress': progress_pct})

    recent_progress = Progress.query.filter_by(user_id=current_user.id).join(
        Lesson, Progress.lesson_id == Lesson.id).order_by(
        Progress.completed_at.desc()).limit(5).all()
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('profile.html', courses_progress=courses_progress, recent_progress=recent_progress, courses_for_ai=all_courses)


@main_bp.route('/lesson/<int:lesson_id>/questions/ask', methods=['POST'])
@login_required
def ask_question(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Check if user is enrolled
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not enrollment:
        flash('Пожалуйста, запишитесь на курс, чтобы задать вопрос.', 'warning')
        return redirect(url_for('main.course_detail', course_id=course.id))
    
    form = AskQuestionForm()
    if form.validate_on_submit():
        attachment_filename = save_file(form.attachment.data, current_app.config['UPLOAD_FOLDER_ATTACHMENTS'])
        question = Question(
            student_id=current_user.id,
            lesson_id=lesson.id,
            body=form.body.data,
            attachment_url=attachment_filename
        )
        db.session.add(question)
        db.session.commit()
        flash('Ваш вопрос отправлен! Ментор ответит в ближайшее время.', 'success')
    
    return redirect(url_for('main.lesson', lesson_id=lesson.id))
