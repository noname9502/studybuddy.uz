from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, flash
from datetime import datetime, timedelta


def mentor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('mentor', 'admin'):
            flash('Доступ только для менторов.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def uzbekistan_time(utc_datetime):
    """Convert UTC datetime to Uzbekistan time (UTC+5)"""
    if utc_datetime is None:
        return None
    return utc_datetime + timedelta(hours=5)


def format_uzbekistan_time(utc_datetime, format_str='%d.%m.%Y %H:%M'):
    """Format UTC datetime as Uzbekistan time string"""
    uz_datetime = uzbekistan_time(utc_datetime)
    if uz_datetime is None:
        return ''
    return uz_datetime.strftime(format_str)
