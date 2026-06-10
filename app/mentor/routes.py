from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.mentor import mentor_bp
from app.utils import mentor_required
from app.extensions import db
from app.models import Question, Answer, MentorCourse, Course, Lesson, User, Enrollment, Progress
from app.mentor.forms import AnswerForm, MentorCourseSelectionForm
import os
import uuid


@mentor_bp.route('/')
@login_required
@mentor_required
def dashboard():
    # Get assigned courses for current mentor
    assigned_course_ids = [mc.course_id for mc in current_user.mentor_courses]
    
    # Get all questions from assigned courses
    total_questions = Question.query.join(Lesson).filter(Lesson.course_id.in_(assigned_course_ids)).count()
    open_questions = Question.query.join(Lesson).filter(Lesson.course_id.in_(assigned_course_ids), Question.status == 'open').count()
    answered_questions = Question.query.join(Lesson).filter(Lesson.course_id.in_(assigned_course_ids), Question.status == 'answered').count()
    
    # Get recent open questions
    recent_open_questions = Question.query.join(Lesson)\
        .filter(Lesson.course_id.in_(assigned_course_ids), Question.status == 'open')\
        .order_by(Question.created_at.desc())\
        .limit(5)\
        .all()
    
    return render_template('mentor/dashboard.html',
                         total_questions=total_questions,
                         open_questions=open_questions,
                         answered_questions=answered_questions,
                         assigned_courses_count=len(assigned_course_ids),
                         recent_open_questions=recent_open_questions)


@mentor_bp.route('/questions')
@login_required
@mentor_required
def questions():
    assigned_course_ids = [mc.course_id for mc in current_user.mentor_courses]
    
    # Filters
    course_filter = request.args.get('course', type=int)
    status_filter = request.args.get('status', '')
    sort_order = request.args.get('sort', 'newest')
    
    query = Question.query.join(Lesson).filter(Lesson.course_id.in_(assigned_course_ids))
    
    if course_filter:
        query = query.filter(Lesson.course_id == course_filter)
    if status_filter:
        query = query.filter(Question.status == status_filter)
    
    if sort_order == 'newest':
        query = query.order_by(Question.created_at.desc())
    else:
        query = query.order_by(Question.created_at.asc())
    
    questions_list = query.all()
    assigned_courses = Course.query.filter(Course.id.in_(assigned_course_ids)).all()
    
    return render_template('mentor/questions_list.html',
                         questions=questions_list,
                         assigned_courses=assigned_courses,
                         course_filter=course_filter,
                         status_filter=status_filter,
                         sort_order=sort_order)


@mentor_bp.route('/questions/<int:question_id>', methods=['GET', 'POST'])
@login_required
@mentor_required
def question_detail(question_id):
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    
    # Check if mentor is assigned to the course of this question
    assigned_course_ids = [mc.course_id for mc in current_user.mentor_courses]
    if question.lesson.course_id not in assigned_course_ids:
        flash('У вас нет доступа к этому вопросу.', 'danger')
        return redirect(url_for('mentor.dashboard'))
    
    if form.validate_on_submit():
        answer = Answer(
            question_id=question_id,
            mentor_id=current_user.id,
            body=form.body.data
        )
        db.session.add(answer)
        question.status = 'answered'
        db.session.commit()
        flash('Ответ отправлен! Студент увидит его на странице урока.', 'success')
        return redirect(url_for('mentor.question_detail', question_id=question_id))
    
    # Get student info
    student = question.student
    student_enrollments = Enrollment.query.filter_by(user_id=student.id).count()
    student_progress = Progress.query.filter_by(user_id=student.id).count()
    
    return render_template('mentor/question_detail.html',
                         question=question,
                         form=form,
                         student=student,
                         student_enrollments=student_enrollments,
                         student_progress=student_progress)


@mentor_bp.route('/courses', methods=['GET', 'POST'])
@login_required
@mentor_required
def courses():
    # Get all available courses
    all_courses = Course.query.filter_by(is_published=True).all()
    # Get current mentor's assigned course ids
    assigned_course_ids = [mc.course_id for mc in current_user.mentor_courses]
    
    form = MentorCourseSelectionForm()
    # Populate form choices with all courses
    form.courses.choices = [(str(course.id), course.title) for course in all_courses]
    
    if form.validate_on_submit():
        # Get selected course ids from form
        selected_course_ids = [int(cid) for cid in form.courses.data]
        
        # Delete all existing assignments for this mentor
        MentorCourse.query.filter_by(mentor_id=current_user.id).delete()
        
        # Add new assignments
        for course_id in selected_course_ids:
            mc = MentorCourse(mentor_id=current_user.id, course_id=course_id)
            db.session.add(mc)
        
        db.session.commit()
        flash('Курсы успешно сохранены!', 'success')
        return redirect(url_for('mentor.courses'))
    
    # If GET request, pre-select already assigned courses
    if request.method == 'GET':
        form.courses.data = [str(cid) for cid in assigned_course_ids]
    
    assigned_courses = [mc.course for mc in current_user.mentor_courses]
    return render_template('mentor/courses.html',
                         assigned_courses=assigned_courses,
                         all_courses=all_courses,
                         form=form)


@mentor_bp.route('/students')
@login_required
@mentor_required
def students():
    assigned_course_ids = [mc.course_id for mc in current_user.mentor_courses]
    # Get all students enrolled in assigned courses
    enrollments = Enrollment.query.filter(Enrollment.course_id.in_(assigned_course_ids)).all()
    student_ids = set(e.user_id for e in enrollments)
    students = User.query.filter(User.id.in_(student_ids)).all()
    return render_template('mentor/students.html', students=students)
