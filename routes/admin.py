from flask import Blueprint, render_template, jsonify, request, send_file, flash, redirect, url_for
from flask_login import login_required
from utils.decorators import admin_required
from utils.helpers import generate_qr_token
from models import db, get_wib_now
from models.user import User
from models.attendance import Attendance
from routes.auth import bcrypt
import qrcode
import io
import base64
from datetime import datetime
import openpyxl

HARI_INDO = {
    0: 'Senin',
    1: 'Selasa',
    2: 'Rabu',
    3: 'Kamis',
    4: 'Jumat',
    5: 'Sabtu',
    6: 'Minggu'
}

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    today = get_wib_now().date()
    
    # Stats
    total_users = User.query.filter_by(role='user').count()
    total_hadir = Attendance.query.filter_by(tanggal=today).count()
    total_belum = total_users - total_hadir
    
    return render_template('admin/dashboard.html', 
                           total_hadir=total_hadir, 
                           total_belum=total_belum,
                           total_users=total_users)

@admin_bp.route('/api/generate_qr')
@login_required
@admin_required
def api_generate_qr():
    token = generate_qr_token()
    
    # Create QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64 string
    buffered = io.BytesIO()
    try:
        img.save(buffered, format="PNG")
    except TypeError:
        img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return jsonify({
        'qr_image': f"data:image/png;base64,{img_str}",
        'token': token
    })

@admin_bp.route('/api/recent_scans')
@login_required
@admin_required
def recent_scans():
    today = get_wib_now().date()
    scans = Attendance.query.filter_by(tanggal=today).order_by(Attendance.created_at.desc()).limit(10).all()
    
    data = []
    for scan in scans:
        data.append({
            'name': scan.user.name,
            'tanggal': f"{HARI_INDO[scan.tanggal.weekday()]}, {scan.tanggal.strftime('%d-%m-%Y')}",
            'jam': scan.jam_absen.strftime('%H:%M:%S'),
            'status': scan.status_absen
        })
        
    return jsonify(data)

@admin_bp.route('/export')
@login_required
@admin_required
def export_excel():
    attendances = Attendance.query.all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Absensi"
    
    headers = ['ID', 'Nama Siswa', 'Hari, Tanggal', 'Jam Absen', 'Waktu Scan Lengkap', 'IP Address', 'Status']
    ws.append(headers)
    
    for a in attendances:
        ws.append([
            a.id,
            a.user.name,
            f"{HARI_INDO[a.tanggal.weekday()]}, {a.tanggal.strftime('%d-%m-%Y')}",
            a.jam_absen.strftime('%H:%M:%S'),
            a.created_at.strftime('%d-%m-%Y %H:%M:%S'),
            a.ip_address,
            a.status_absen
        ])
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name=f"rekap_absensi_{get_wib_now().strftime('%Y%m%d')}.xlsx",
        as_attachment=True
    )


# --- USER MANAGEMENT ROUTES ---

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users_list = User.query.filter_by(role='user').all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not name or not email or not password:
        flash('Semua field harus diisi!', 'danger')
        return redirect(url_for('admin.users'))
        
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email sudah terdaftar!', 'danger')
        return redirect(url_for('admin.users'))
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=name, email=email, password=hashed_password, role='user')
    
    db.session.add(new_user)
    db.session.commit()
    
    flash('Siswa berhasil ditambahkan!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Tidak dapat mengedit admin melalui form ini!', 'danger')
        return redirect(url_for('admin.users'))
        
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name or not email:
        flash('Nama dan Email harus diisi!', 'danger')
        return redirect(url_for('admin.users'))
        
    # Check if email is used by someone else
    existing_user = User.query.filter(User.email == email, User.id != user_id).first()
    if existing_user:
        flash('Email sudah terdaftar untuk pengguna lain!', 'danger')
        return redirect(url_for('admin.users'))
        
    user.name = name
    user.email = email
    db.session.commit()
    
    flash('Data siswa berhasil diubah!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/reset_pwd/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Tidak dapat mereset password admin melalui form ini!', 'danger')
        return redirect(url_for('admin.users'))
        
    new_password = request.form.get('new_password')
    if not new_password:
        flash('Password baru tidak boleh kosong!', 'danger')
        return redirect(url_for('admin.users'))
        
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    
    flash('Password siswa berhasil direset!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Tidak dapat menghapus admin!', 'danger')
        return redirect(url_for('admin.users'))
        
    # Delete related attendances first
    Attendance.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash('Siswa berhasil dihapus!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/export')
@login_required
@admin_required
def export_users_excel():
    users_list = User.query.filter_by(role='user').all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Siswa"
    
    headers = ['ID', 'Nama Siswa', 'Email', 'Role']
    ws.append(headers)
    
    for u in users_list:
        ws.append([u.id, u.name, u.email, u.role])
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name=f"data_siswa_{get_wib_now().strftime('%Y%m%d')}.xlsx",
        as_attachment=True
    )

@admin_bp.route('/users/import', methods=['POST'])
@login_required
@admin_required
def import_users_excel():
    if 'file' not in request.files:
        flash('File tidak ditemukan.', 'danger')
        return redirect(url_for('admin.users'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(url_for('admin.users'))
        
    if not file.filename.endswith('.xlsx'):
        flash('Format file harus .xlsx', 'danger')
        return redirect(url_for('admin.users'))
        
    try:
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        
        success_count = 0
        error_count = 0
        
        # Assume row 1 is header: Nama, Email, Password
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 3:
                continue
                
            name, email, password = row[0], row[1], row[2]
            if not name or not email or not password:
                error_count += 1
                continue
                
            # Check if email exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error_count += 1
                continue
                
            hashed_password = bcrypt.generate_password_hash(str(password)).decode('utf-8')
            new_user = User(name=str(name), email=str(email), password=hashed_password, role='user')
            db.session.add(new_user)
            success_count += 1
            
        db.session.commit()
        
        if success_count > 0:
            flash(f'Berhasil import {success_count} data siswa. Gagal/Skip: {error_count} baris.', 'success')
        else:
            flash(f'Tidak ada data yang diimport. Mungkin format salah atau email sudah terdaftar. Gagal: {error_count} baris.', 'warning')
            
    except Exception as e:
        flash(f'Gagal memproses file Excel: {str(e)}', 'danger')
        
    return redirect(url_for('admin.users'))
