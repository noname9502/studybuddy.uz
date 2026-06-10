from app import create_app
from app.extensions import db
from app.models import User, Course, Lesson, Enrollment, Comment, Rating, Question, Answer, MentorCourse, ParentChildLink, Progress
from datetime import datetime, timedelta


def seed():
    app = create_app()

    with app.app_context():
        db.create_all()

        print("Создаем администратора...")
        admin = User(username='admin', email='admin@studybuddy.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        print("Создаем студентов...")
        student1 = User(username='ivan', email='ivan@example.com')
        student1.set_password('password123')
        db.session.add(student1)

        student2 = User(username='maria', email='maria@example.com')
        student2.set_password('password123')
        db.session.add(student2)

        print("Создаем ментора...")
        mentor = User(username='mentor1', email='mentor@studybuddy.com', role='mentor')
        mentor.set_password('mentor123')
        db.session.add(mentor)

        print("Создаем родителя...")
        parent = User(username='parent', email='parent@example.com', role='parent')
        parent.set_password('parent123')
        db.session.add(parent)

        db.session.commit()

        print("Создаем курсы...")
        course1 = Course(
            title='Python для начинающих',
            description='Полный курс по программированию на Python с нуля. Научитесь основам и создавайте свои первые проекты.',
            category='Программирование',
            level='beginner',
            is_published=True,
            created_by=admin.id
        )
        db.session.add(course1)

        course2 = Course(
            title='Основы математики',
            description='Курс по базовым математическим концепциям: алгебра, геометрия, анализ.',
            category='Математика',
            level='beginner',
            is_published=True,
            created_by=admin.id
        )
        db.session.add(course2)

        course3 = Course(
            title='Веб-дизайн базовый',
            description='Изучите основы дизайна интерфейсов, работу с цветами, типографикой и композицией.',
            category='Дизайн',
            level='beginner',
            is_published=True,
            created_by=admin.id
        )
        db.session.add(course3)

        db.session.commit()

        print("Назначаем ментора к курсам...")
        mc1 = MentorCourse(mentor_id=mentor.id, course_id=course1.id)
        mc2 = MentorCourse(mentor_id=mentor.id, course_id=course2.id)
        mc3 = MentorCourse(mentor_id=mentor.id, course_id=course3.id)
        db.session.add(mc1)
        db.session.add(mc2)
        db.session.add(mc3)

        print("Создаем уроки...")
        lesson1 = Lesson(
            course_id=course1.id,
            title='Введение в Python',
            description='Узнайте, что такое Python и как установить его на ваш компьютер.',
            video_url='placeholder.mp4',
            duration=300,
            order_index=1,
            is_published=True
        )
        db.session.add(lesson1)

        lesson2 = Lesson(
            course_id=course1.id,
            title='Переменные и типы данных',
            description='Изучите основные типы данных в Python: int, float, string, bool.',
            video_url='placeholder.mp4',
            duration=450,
            order_index=2,
            is_published=True
        )
        db.session.add(lesson2)

        lesson3 = Lesson(
            course_id=course2.id,
            title='Введение в алгебру',
            description='Основные понятия алгебры: выражения, уравнения, функции.',
            video_url='placeholder.mp4',
            duration=600,
            order_index=1,
            is_published=True
        )
        db.session.add(lesson3)

        lesson4 = Lesson(
            course_id=course3.id,
            title='Теория цвета',
            description='Как выбирать цвета для дизайна, цветовые схемы и сочетания.',
            video_url='placeholder.mp4',
            duration=400,
            order_index=1,
            is_published=True
        )
        db.session.add(lesson4)

        db.session.commit()

        print("Создаем записи на курсы...")
        enrollment1 = Enrollment(user_id=student1.id, course_id=course1.id)
        db.session.add(enrollment1)

        enrollment2 = Enrollment(user_id=student2.id, course_id=course2.id)
        db.session.add(enrollment2)

        db.session.commit()

        print("Создаем комментарии...")
        comment1 = Comment(
            lesson_id=lesson1.id,
            user_id=student1.id,
            body='Отличный урок! Все понятно.'
        )
        db.session.add(comment1)

        comment2 = Comment(
            lesson_id=lesson3.id,
            user_id=student2.id,
            body='Очень полезный материал, спасибо!'
        )
        db.session.add(comment2)

        print("Создаем оценки...")
        rating1 = Rating(
            lesson_id=lesson1.id,
            user_id=student1.id,
            score=5
        )
        db.session.add(rating1)

        print("Создаем вопросы...")
        question1 = Question(
            student_id=student1.id,
            lesson_id=lesson1.id,
            body='Как установить Python на Windows?',
            status='open'
        )
        db.session.add(question1)

        question2 = Question(
            student_id=student2.id,
            lesson_id=lesson3.id,
            body='Чем отличается алгебра от геометрии?',
            status='open'
        )
        db.session.add(question2)

        question3 = Question(
            student_id=student1.id,
            lesson_id=lesson2.id,
            body='Что такое тип данных int?',
            status='answered'
        )
        db.session.add(question3)

        db.session.commit()

        print("Создаем ответ на вопрос...")
        answer1 = Answer(
            question_id=question3.id,
            mentor_id=mentor.id,
            body='int — это целочисленный тип данных в Python, который хранит целые числа без десятичной точки.'
        )
        db.session.add(answer1)

        db.session.commit()

        print("Создаем связь родитель-ребенок...")
        parent_child_link = ParentChildLink(parent_id=parent.id, child_id=student1.id)
        db.session.add(parent_child_link)
        
        print("Создаем прогресс для студента...")
        progress1 = Progress(user_id=student1.id, lesson_id=lesson1.id, watched=True, completed_at=datetime.utcnow() - timedelta(days=1))
        db.session.add(progress1)

        db.session.commit()

        print("Данные успешно загружены!")
        print("")
        print("Данные для входа:")
        print("Администратор: admin@studybuddy.com / admin123")
        print("Ментор: mentor@studybuddy.com / mentor123")
        print("Родитель: parent@example.com / parent123")
        print("Студент 1: ivan@example.com / password123")
        print("Студент 2: maria@example.com / password123")


if __name__ == '__main__':
    seed()
