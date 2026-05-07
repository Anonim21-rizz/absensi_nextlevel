from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import pytz

db = SQLAlchemy()

def get_wib_now():
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(tz)
