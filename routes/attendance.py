from flask import Blueprint, render_template, request, jsonify, session
from models import db, get_wib_now
from models.attendance import Attendance
from models.user import User
from routes.auth import bcrypt
from utils.helpers import decode_qr_token, get_device_fingerprint
import uuid

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/scan')
def scan():
    # Public route, no login required
    if 'session_token' not in session:
        session['session_token'] = str(uuid.uuid4())
        
    return render_template('user/scan.html')

@attendance_bp.route('/api/submit_scan', methods=['POST'])
def submit_scan():
    data = request.json
    token = data.get('token')
    device_uuid = data.get('device_id')
    name = data.get('name')
    password = data.get('password')
    
    if not token:
        return jsonify({'status': 'error', 'message': 'Token tidak ditemukan.'}), 400
        
    if not name or not password:
        return jsonify({'status': 'error', 'message': 'Nama dan Password harus diisi.'}), 400
        
    # Verify User (case-insensitive name match)
    user = User.query.filter(User.name.ilike(name), User.role == 'user').first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'status': 'error', 'message': 'Nama atau Password salah.'}), 401
        
    if user.role == 'admin':
        return jsonify({'status': 'error', 'message': 'Admin tidak bisa absen di sini.'}), 403
        
    # Decode token
    payload = decode_qr_token(token)
    if 'error' in payload:
        return jsonify({'status': 'error', 'message': payload['error']}), 400
        
    today = get_wib_now().date()
    
    # Check if user already attended today
    already_attended = Attendance.query.filter_by(user_id=user.id, tanggal=today).first()
    if already_attended:
        return jsonify({'status': 'error', 'message': 'Anda sudah melakukan absensi hari ini.'}), 400
        
    # Check if device already used today
    browser_fp = get_device_fingerprint(request)
    device_id = f"{device_uuid}-{browser_fp}"
    
    device_used = Attendance.query.filter_by(device_id=device_id, tanggal=today).first()
    if device_used:
        return jsonify({'status': 'error', 'message': 'Perangkat ini sudah digunakan untuk absen hari ini.'}), 400
        
    session_token = session.get('session_token', str(uuid.uuid4()))
    
    # Get IP
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
        
    # All validations passed, save attendance
    now = get_wib_now()
    new_attendance = Attendance(
        user_id=user.id,
        tanggal=today,
        jam_absen=now.time(),
        ip_address=ip_address,
        device_id=device_id,
        browser_info=request.headers.get('User-Agent', 'Unknown'),
        session_token=session_token,
        qr_token=token,
        status_absen='Hadir'
    )
    
    db.session.add(new_attendance)
    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Absensi berhasil dicatat.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Terjadi kesalahan pada server.'}), 500
