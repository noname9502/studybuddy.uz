from functools import wraps
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.parent import parent_bp
from app.extensions import db
from app.models import User, ParentChildLink, Course, Lesson, Enrollment, Progress
from datetime import datetime, timedelta


def parent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('parent', 'admin'):
            flash('Доступ только для родителей.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@parent_bp.route('/')
@login_required
@parent_required
def dashboard():
    # Get all children for this parent
    child_links = ParentChildLink.query.filter_by(parent_id=current_user.id).all()
    children = [link.child for link in child_links]
    
    # Prepare data for each child
    children_data = []
    for child in children:
        # Get enrollments
        enrollments = Enrollment.query.filter_by(user_id=child.id).all()
        # Calculate progress for each enrolled course
        courses_progress = []
        for enrollment in enrollments:
            course = enrollment.course
            total_lessons = Lesson.query.filter_by(course_id=course.id, is_published=True).count()
            completed_lessons = Progress.query.filter_by(user_id=child.id, watched=True).join(Lesson).filter(Lesson.course_id == course.id).count()
            progress_percent = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            courses_progress.append({
                'course': course,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress_percent': round(progress_percent, 1)
            })
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_progress = Progress.query.filter_by(user_id=child.id)\
            .filter(Progress.completed_at >= seven_days_ago)\
            .order_by(Progress.completed_at.desc())\
            .limit(10)\
            .all()
        
        children_data.append({
            'child': child,
            'enrollments_count': len(enrollments),
            'courses_progress': courses_progress,
            'recent_progress': recent_progress
        })
    
    return render_template('parent/dashboard.html',
                         children=children_data,
                         children_count=len(children))


@parent_bp.route('/link-child', methods=['GET', 'POST'])
@login_required
@parent_required
def link_child():
    if request.method == 'POST':
        child_email = request.form.get('child_email')
        child = User.query.filter_by(email=child_email).first()
        
        if not child:
            flash('Пользователь с таким email не найден.', 'danger')
            return redirect(url_for('parent.link_child'))
        
        if child.id == current_user.id:
            flash('Вы не можете связать себя с собой.', 'danger')
            return redirect(url_for('parent.link_child'))
        
        # Check if already linked
        existing_link = ParentChildLink.query.filter_by(parent_id=current_user.id, child_id=child.id).first()
        if existing_link:
            flash('Этот ребенок уже связан с вашим аккаунтом.', 'warning')
            return redirect(url_for('parent.dashboard'))
        
        # Create link
        link = ParentChildLink(parent_id=current_user.id, child_id=child.id)
        db.session.add(link)
        db.session.commit()
        
        flash(f'Ребенок {child.username} успешно связан с вашим аккаунтом!', 'success')
        return redirect(url_for('parent.dashboard'))
    
    return render_template('parent/link_child.html')


@parent_bp.route('/child/<int:child_id>')
@login_required
@parent_required
def child_detail(child_id):
    # Check if parent is linked to this child
    link = ParentChildLink.query.filter_by(parent_id=current_user.id, child_id=child_id).first()
    if not link:
        flash('У вас нет доступа к этому ребенку.', 'danger')
        return redirect(url_for('parent.dashboard'))
    
    child = User.query.get_or_404(child_id)
    
    # Get enrollments
    enrollments = Enrollment.query.filter_by(user_id=child.id).all()
    courses_progress = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = Lesson.query.filter_by(course_id=course.id, is_published=True).count()
        completed_lessons = Progress.query.filter_by(user_id=child.id, watched=True).join(Lesson).filter(Lesson.course_id == course.id).count()
        progress_percent = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        # Get lessons details
        lessons = Lesson.query.filter_by(course_id=course.id, is_published=True).order_by(Lesson.order_index).all()
        lesson_details = []
        for lesson in lessons:
            progress = Progress.query.filter_by(user_id=child.id, lesson_id=lesson.id).first()
            lesson_details.append({
                'lesson': lesson,
                'progress': progress
            })
        
        courses_progress.append({
            'course': course,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': round(progress_percent, 1),
            'lessons': lesson_details
        })
    
    # All progress history
    all_progress = Progress.query.filter_by(user_id=child.id).order_by(Progress.completed_at.desc()).all()
    
    return render_template('parent/child_detail.html',
                         child=child,
                         courses_progress=courses_progress,
                         all_progress=all_progress)
