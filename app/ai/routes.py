from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Course, Enrollment
import os
from dotenv import load_dotenv
import openai

load_dotenv()

ai_bp = Blueprint('ai', __name__)

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


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


@ai_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '')

    courses = Course.query.filter_by(is_published=True).all()
    courses_context = []
    for course in courses:
        courses_context.append(f"- {course.title}: {course.description} (Category: {course.category}, Level: {course.level})")
    
    system_prompt = """You are StudyBuddy AI Assistant, a helpful and professional AI that helps users with general questions and course recommendations.

When users ask about course recommendations:
1. Ask clarifying questions about their interests, goals, skills, or needs if needed
2. Use the available courses information to suggest suitable courses
3. Be friendly and encouraging

Available courses:
{courses}

Respond in Russian (or the language the user uses) in a clear, accurate, and user-friendly way.
""".format(courses='\n'.join(courses_context) if courses_context else 'No courses available yet.')

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        ai_response = response.choices[0].message.content
        return jsonify({'success': True, 'response': ai_response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/recommendations', methods=['POST'])
@login_required
def recommendations():
    data = request.get_json()
    interests = data.get('interests', '')
    goals = data.get('goals', '')
    skills = data.get('skills', '')

    courses = get_course_recommendations(interests, goals, skills)
    return jsonify({'success': True, 'courses': courses})
