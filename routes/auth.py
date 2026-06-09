from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({
                'status': 'success',
                'role': current_user.role,
                'name': current_user.name,
                'redirect': url_for('admin.dashboard') if current_user.role == 'admin' else url_for('attendance.scan')
            })
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('attendance.scan'))
            
    if request.method == 'POST':
        if request.is_json:
            data = request.json
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'status': 'success',
                    'role': user.role,
                    'name': user.name,
                    'redirect': url_for('admin.dashboard') if user.role == 'admin' else url_for('attendance.scan')
                })
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('attendance.scan'))
        else:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'status': 'error', 'message': 'Login gagal. Periksa email dan password Anda.'}), 401
            flash('Login gagal. Periksa email dan password Anda.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

