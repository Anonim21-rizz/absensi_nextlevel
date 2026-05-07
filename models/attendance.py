from . import db, get_wib_now
from sqlalchemy import UniqueConstraint

class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    jam_absen = db.Column(db.Time, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    device_id = db.Column(db.String(255), nullable=False)
    browser_info = db.Column(db.String(255), nullable=False)
    session_token = db.Column(db.String(255), nullable=False)
    qr_token = db.Column(db.String(500), nullable=False)
    status_absen = db.Column(db.String(20), nullable=False, default='Hadir')
    created_at = db.Column(db.DateTime, default=get_wib_now)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'tanggal', name='_user_tanggal_uc'),
        UniqueConstraint('device_id', 'tanggal', name='_device_tanggal_uc'),
    )
