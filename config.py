import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///studybuddy.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    UPLOAD_FOLDER_VIDEOS = 'app/static/uploads/videos'
    UPLOAD_FOLDER_THUMBNAILS = 'app/static/uploads/thumbnails'
    UPLOAD_FOLDER_ATTACHMENTS = 'app/static/uploads/attachments'
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
