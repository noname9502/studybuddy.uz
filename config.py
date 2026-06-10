import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'instance', 'studybuddy.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    UPLOAD_FOLDER_VIDEOS = os.path.join(basedir, 'app', 'static', 'uploads', 'videos')
    UPLOAD_FOLDER_THUMBNAILS = os.path.join(basedir, 'app', 'static', 'uploads', 'thumbnails')
    UPLOAD_FOLDER_ATTACHMENTS = os.path.join(basedir, 'app', 'static', 'uploads', 'attachments')
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
