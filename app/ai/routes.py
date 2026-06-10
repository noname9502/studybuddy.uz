from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Course

ai_bp = Blueprint('ai', __name__)


def get_course_recommendations(user_interests=None, user_goals=None, user_skills=None):
    courses = Course.query.filter_by(is_published=True).all()
    courses_data = []
    for course in courses:
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'category': course.category,
            'level': course.level
        })
    return courses_data


@ai_bp.route('/assistant')
@login_required
def assistant():
    courses = [c.to_dict() for c in Course.query.filter_by(is_published=True).all()]
    return render_template('ai/assistant.html', courses=courses)


@ai_bp.route('/api/recommendations', methods=['POST'])
@login_required
def recommendations():
    data = request.get_json()
    interests = data.get('interests', '')
    goals = data.get('goals', '')
    skills = data.get('skills', '')

    courses = get_course_recommendations(interests, goals, skills)
    return jsonify({'success': True, 'courses': courses})
