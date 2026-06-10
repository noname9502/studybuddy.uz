from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
import os
import uuid
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import User, Course, Lesson, Enrollment, Comment, Rating, Question, Answer, MentorCourse, Progress
from app.admin.forms import CourseForm, LessonForm, UserCreateForm, UserEditForm, EnrollmentForm

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('У вас нет прав для доступа к этой странице.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def save_file(file, upload_folder):
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None


def delete_file(filename, upload_folder):
    if filename:
        filepath = os.path.join(upload_folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    from datetime import datetime, timedelta
    
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_lessons = Lesson.query.count()
    total_ratings = Rating.query.count()
    total_comments = Comment.query.count()
    total_enrollments = Enrollment.query.count()

    recent_enrollments = Enrollment.query.order_by(Enrollment.enrolled_at.desc()).limit(10).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(10).all()

    top_courses = db.session.query(
        Course,
        db.func.count(Enrollment.id).label('enrollment_count')
    ).join(Enrollment, Course.id == Enrollment.course_id)\
     .group_by(Course.id)\
     .order_by(db.func.count(Enrollment.id).desc())\
     .limit(5).all()
    top_courses = [{'title': course.title, 'enrollment_count': count} for course, count in top_courses]

    chart_labels = []
    users_data = []
    enrollments_data = []
    
    for i in range(6, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime('%d.%m')
        chart_labels.append(date_str)
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        user_count = User.query.filter(
            User.created_at >= start_date,
            User.created_at < end_date
        ).count()
        users_data.append(user_count)
        
        enrollment_count = Enrollment.query.filter(
            Enrollment.enrolled_at >= start_date,
            Enrollment.enrolled_at < end_date
        ).count()
        enrollments_data.append(enrollment_count)
    
    chart_data = {
        'labels': chart_labels,
        'users': users_data,
        'enrollments': enrollments_data
    }

    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_courses=total_courses,
                         total_lessons=total_lessons,
                         total_ratings=total_ratings,
                         total_comments=total_comments,
                         total_enrollments=total_enrollments,
                         recent_enrollments=recent_enrollments,
                         recent_comments=recent_comments,
                         top_courses=top_courses,
                         chart_data=chart_data,
                         courses_for_ai=all_courses)


@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
@admin_required
def courses():
    if request.method == 'POST':
        action = request.form.get('action')
        course_ids = request.form.getlist('course_ids')
        
        if action and course_ids:
            courses = Course.query.filter(Course.id.in_(course_ids)).all()
            
            if action == 'publish':
                for course in courses:
                    course.is_published = True
                flash(f'{len(courses)} курс(ов) опубликовано!', 'success')
            elif action == 'unpublish':
                for course in courses:
                    course.is_published = False
                flash(f'{len(courses)} курс(ов) снято с публикации!', 'success')
            elif action == 'delete':
                for course in courses:
                    # Delete MentorCourse for this course
                    MentorCourse.query.filter_by(course_id=course.id).delete()
                    # Delete lessons and their related data
                    lessons = Lesson.query.filter_by(course_id=course.id).all()
                    for lesson in lessons:
                        delete_file(lesson.video_url, current_app.config['UPLOAD_FOLDER_VIDEOS'])
                        # Delete lesson-related records manually
                        Answer.query.filter(Answer.question.has(lesson_id=lesson.id)).delete()
                        Question.query.filter_by(lesson_id=lesson.id).delete()
                        Comment.query.filter_by(lesson_id=lesson.id).delete()
                        Rating.query.filter_by(lesson_id=lesson.id).delete()
                        Progress.query.filter_by(lesson_id=lesson.id).delete()
                        Lesson.query.filter_by(id=lesson.id).delete()
                    # Delete enrollments
                    Enrollment.query.filter_by(course_id=course.id).delete()
                    # Delete thumbnail
                    delete_file(course.thumbnail_url, current_app.config['UPLOAD_FOLDER_THUMBNAILS'])
                    # Delete course
                    db.session.delete(course)
                flash(f'{len(courses)} курс(ов) удалено!', 'success')
            
            db.session.commit()
        
        return redirect(url_for('admin.courses'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    level = request.args.get('level', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')
    
    query = Course.query
    
    if search:
        query = query.filter(Course.title.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if status:
        query = query.filter_by(is_published=(status == 'published'))
    
    if sort_dir == 'desc':
        query = query.order_by(getattr(Course, sort_by).desc())
    else:
        query = query.order_by(getattr(Course, sort_by))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    courses = pagination.items
    
    categories = ['Программирование', 'Математика', 'Наука', 'Дизайн', 'Бизнес', 'Языки', 'Другое']
    levels = ['beginner', 'intermediate', 'advanced']
    
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/courses/list.html', 
                         courses=courses, 
                         pagination=pagination,
                         search=search,
                         category=category,
                         level=level,
                         status=status,
                         sort_by=sort_by,
                         sort_dir=sort_dir,
                         categories=categories,
                         levels=levels,
                         courses_for_ai=all_courses)


@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_course():
    form = CourseForm()
    if form.validate_on_submit():
        thumbnail_filename = save_file(form.thumbnail.data, current_app.config['UPLOAD_FOLDER_THUMBNAILS'])
        course = Course(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            level=form.level.data,
            thumbnail_url=thumbnail_filename,
            is_published=form.is_published.data,
            created_by=current_user.id
        )
        db.session.add(course)
        db.session.commit()
        flash('Курс создан!', 'success')
        return redirect(url_for('admin.courses'))
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/courses/create.html', form=form, courses_for_ai=all_courses)


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.category = form.category.data
        course.level = form.level.data
        course.is_published = form.is_published.data

        if form.thumbnail.data:
            delete_file(course.thumbnail_url, current_app.config['UPLOAD_FOLDER_THUMBNAILS'])
            course.thumbnail_url = save_file(form.thumbnail.data, current_app.config['UPLOAD_FOLDER_THUMBNAILS'])

        db.session.commit()
        flash('Курс обновлен!', 'success')
        return redirect(url_for('admin.courses'))

    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/courses/edit.html', form=form, course=course, courses_for_ai=all_courses)


@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Delete all related records manually
    # First, delete MentorCourse for this course
    MentorCourse.query.filter_by(course_id=course_id).delete()
    # Then delete lessons (and their related data via cascades)
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    for lesson in lessons:
        delete_file(lesson.video_url, current_app.config['UPLOAD_FOLDER_VIDEOS'])
        # Delete lesson-related records manually
        Answer.query.filter(Answer.question.has(lesson_id=lesson.id)).delete()
        Question.query.filter_by(lesson_id=lesson.id).delete()
        Comment.query.filter_by(lesson_id=lesson.id).delete()
        Rating.query.filter_by(lesson_id=lesson.id).delete()
        Progress.query.filter_by(lesson_id=lesson.id).delete()
        Lesson.query.filter_by(id=lesson.id).delete()
    # Then delete enrollments
    Enrollment.query.filter_by(course_id=course_id).delete()
    
    # Delete course thumbnail
    delete_file(course.thumbnail_url, current_app.config['UPLOAD_FOLDER_THUMBNAILS'])
    # Delete the course
    db.session.delete(course)
    db.session.commit()
    flash('Курс удален!', 'success')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/publish', methods=['POST'])
@login_required
@admin_required
def publish_course(course_id):
    course = Course.query.get_or_404(course_id)
    course.is_published = not course.is_published
    db.session.commit()
    return jsonify({'success': True, 'is_published': course.is_published})


@admin_bp.route('/lessons')
@login_required
@admin_required
def lessons():
    course_id = request.args.get('course_id', type=int)
    query = Lesson.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    lessons = query.all()
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/lessons/list.html', lessons=lessons, course_id=course_id, courses_for_ai=all_courses)


@admin_bp.route('/lessons/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_lesson():
    course_id = request.args.get('course_id', type=int)
    form = LessonForm()
    form.course.choices = [(c.id, c.title) for c in Course.query.all()]
    if course_id and not form.is_submitted():
        form.course.data = course_id
    if form.validate_on_submit():
        video_filename = save_file(form.video.data, current_app.config['UPLOAD_FOLDER_VIDEOS'])
        lesson = Lesson(
            course_id=form.course.data,
            title=form.title.data,
            description=form.description.data,
            video_url=video_filename,
            duration=form.duration.data,
            order_index=form.order_index.data,
            is_published=form.is_published.data
        )
        db.session.add(lesson)
        db.session.commit()
        flash('Урок создан!', 'success')
        return redirect(url_for('admin.lessons'))
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/lessons/create.html', form=form, courses_for_ai=all_courses)


@admin_bp.route('/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonForm(obj=lesson)
    form.course.choices = [(c.id, c.title) for c in Course.query.all()]
    if form.validate_on_submit():
        lesson.course_id = form.course.data
        lesson.title = form.title.data
        lesson.description = form.description.data
        lesson.duration = form.duration.data
        lesson.order_index = form.order_index.data
        lesson.is_published = form.is_published.data

        if form.video.data:
            delete_file(lesson.video_url, current_app.config['UPLOAD_FOLDER_VIDEOS'])
            lesson.video_url = save_file(form.video.data, current_app.config['UPLOAD_FOLDER_VIDEOS'])

        db.session.commit()
        flash('Урок обновлен!', 'success')
        return redirect(url_for('admin.lessons'))

    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/lessons/edit.html', form=form, lesson=lesson, courses_for_ai=all_courses)


@admin_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Delete related records manually first
    Answer.query.filter(Answer.question.has(lesson_id=lesson_id)).delete()
    Question.query.filter_by(lesson_id=lesson_id).delete()
    Comment.query.filter_by(lesson_id=lesson_id).delete()
    Rating.query.filter_by(lesson_id=lesson_id).delete()
    Progress.query.filter_by(lesson_id=lesson_id).delete()
    
    # Delete the video file
    delete_file(lesson.video_url, current_app.config['UPLOAD_FOLDER_VIDEOS'])
    
    # Delete the lesson
    db.session.delete(lesson)
    db.session.commit()
    flash('Урок удален!', 'success')
    return redirect(url_for('admin.lessons'))


@admin_bp.route('/lessons/<int:lesson_id>/publish', methods=['POST'])
@login_required
@admin_required
def publish_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    lesson.is_published = not lesson.is_published
    db.session.commit()
    return jsonify({'success': True, 'is_published': lesson.is_published})


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')
    
    query = User.query
    
    if search:
        query = query.filter(User.username.ilike(f'%{search}%') | User.email.ilike(f'%{search}%'))
    if role:
        query = query.filter_by(role=role)
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    
    if sort_dir == 'desc':
        query = query.order_by(getattr(User, sort_by).desc())
    else:
        query = query.order_by(getattr(User, sort_by))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/users/list.html', 
                         users=users, 
                         pagination=pagination,
                         search=search,
                         role=role,
                         status=status,
                         sort_by=sort_by,
                         sort_dir=sort_dir,
                         courses_for_ai=all_courses)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.new_password.data:
            user.set_password(form.new_password.data)
        db.session.commit()
        flash('Пользователь обновлен!', 'success')
        return redirect(url_for('admin.users'))
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/users/edit.html', form=form, user=user, courses_for_ai=all_courses)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Вы не можете удалить себя!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Delete all related records manually to avoid foreign key issues
    # Delete answers first (they depend on questions)
    Answer.query.filter_by(mentor_id=user.id).delete()
    # Then delete questions
    Question.query.filter_by(student_id=user.id).delete()
    # Then delete other related records
    MentorCourse.query.filter_by(mentor_id=user.id).delete()
    Comment.query.filter_by(user_id=user.id).delete()
    Rating.query.filter_by(user_id=user.id).delete()
    Progress.query.filter_by(user_id=user.id).delete()
    Enrollment.query.filter_by(user_id=user.id).delete()
    
    # Now delete the user
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удален!', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/comments')
@login_required
@admin_required
def comments():
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/comments/list.html', comments=comments, courses_for_ai=all_courses)


@admin_bp.route('/comments/<int:comment_id>/hide', methods=['POST'])
@login_required
@admin_required
def hide_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_visible = not comment.is_visible
    db.session.commit()
    return jsonify({'success': True, 'is_visible': comment.is_visible})


@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Комментарий удален!', 'success')
    return redirect(url_for('admin.comments'))


@admin_bp.route('/ratings')
@login_required
@admin_required
def ratings():
    ratings = Rating.query.order_by(Rating.created_at.desc()).all()
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/ratings/list.html', ratings=ratings, courses_for_ai=all_courses)


@admin_bp.route('/ratings/<int:rating_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)
    db.session.delete(rating)
    db.session.commit()
    flash('Рейтинг удален!', 'success')
    return redirect(url_for('admin.ratings'))


@admin_bp.route('/enrollments/<int:enrollment_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    form = EnrollmentForm(current_enrollment_id=enrollment_id)
    form.user.choices = [(u.id, u.username) for u in User.query.all()]
    form.course.choices = [(c.id, c.title) for c in Course.query.all()]
    
    if form.validate_on_submit():
        try:
            enrollment.user_id = form.user.data
            enrollment.course_id = form.course.data
            db.session.commit()
            flash('Запись обновлена!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка: этот пользователь уже записан на этот курс!', 'danger')
    
    if request.method == 'GET':
        form.user.data = enrollment.user_id
        form.course.data = enrollment.course_id
    
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/enrollments/edit.html', form=form, enrollment=enrollment, courses_for_ai=all_courses)


@admin_bp.route('/enrollments/<int:enrollment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash('Запись удалена!', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    users_by_date = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).group_by(db.func.date(User.created_at)).all()
    enrollments_by_date = db.session.query(
        db.func.date(Enrollment.enrolled_at).label('date'),
        db.func.count(Enrollment.id).label('count')
    ).group_by(db.func.date(Enrollment.enrolled_at)).all()
    return jsonify({
        'users': [{'date': str(d), 'count': c} for d, c in users_by_date],
        'enrollments': [{'date': str(d), 'count': c} for d, c in enrollments_by_date]
    })


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserCreateForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует!', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data,
                is_active=form.is_active.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Пользователь создан!', 'success')
            return redirect(url_for('admin.users'))
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/users/create.html', form=form, courses_for_ai=all_courses)


@admin_bp.route('/mentors')
@login_required
@admin_required
def mentors():
    mentors = User.query.filter_by(role='mentor').all()
    all_courses = Course.query.all()
    return render_template('admin/mentors.html', mentors=mentors, all_courses=all_courses)


@admin_bp.route('/mentors/<int:mentor_id>/courses', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_mentor_courses(mentor_id):
    mentor = User.query.get_or_404(mentor_id)
    all_courses = Course.query.all()
    assigned_course_ids = [mc.course_id for mc in mentor.mentor_courses]
    
    if request.method == 'POST':
        selected_course_ids = request.form.getlist('course_ids')
        selected_course_ids = [int(cid) for cid in selected_course_ids]
        
        # Delete existing assignments
        MentorCourse.query.filter_by(mentor_id=mentor_id).delete()
        
        # Add new assignments
        for course_id in selected_course_ids:
            mc = MentorCourse(mentor_id=mentor_id, course_id=course_id)
            db.session.add(mc)
        
        db.session.commit()
        flash(f'Курсы для ментора {mentor.username} обновлены!', 'success')
        return redirect(url_for('admin.mentors'))
    
    all_courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('admin/mentors/courses.html', 
                         mentor=mentor, 
                         all_courses=Course.query.all(), 
                         assigned_course_ids=assigned_course_ids,
                         courses_for_ai=all_courses)


@admin_bp.route('/users/<int:user_id>/make-mentor', methods=['POST'])
@login_required
@admin_required
def make_mentor(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'mentor'
    db.session.commit()
    flash(f'Пользователь {user.username} теперь ментор!', 'success')
    return redirect(url_for('admin.mentors'))


@admin_bp.route('/users/<int:user_id>/make-student', methods=['POST'])
@login_required
@admin_required
def make_student(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'student'
    # Remove all mentor course assignments
    MentorCourse.query.filter_by(mentor_id=user.id).delete()
    db.session.commit()
    flash(f'Пользователь {user.username} теперь студент!', 'success')
    return redirect(url_for('admin.mentors'))


@admin_bp.route('/mentors/<int:mentor_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_mentor(mentor_id):
    mentor = User.query.get_or_404(mentor_id)
    course_ids = request.form.getlist('course_ids')
    
    for course_id in course_ids:
        course_id = int(course_id)
        # Check if already assigned
        existing = MentorCourse.query.filter_by(mentor_id=mentor_id, course_id=course_id).first()
        if not existing:
            mc = MentorCourse(mentor_id=mentor_id, course_id=course_id)
            db.session.add(mc)
    
    db.session.commit()
    flash(f'Курсы назначены ментору {mentor.username}!', 'success')
    return redirect(url_for('admin.mentors'))


@admin_bp.route('/mentors/<int:mentor_id>/unassign', methods=['POST'])
@login_required
@admin_required
def unassign_mentor(mentor_id):
    mentor = User.query.get_or_404(mentor_id)
    course_id = request.form.get('course_id', type=int)
    
    if course_id:
        MentorCourse.query.filter_by(mentor_id=mentor_id, course_id=course_id).delete()
        db.session.commit()
        flash(f'Курс удален у ментора {mentor.username}!', 'success')
    
    return redirect(url_for('admin.mentors'))
