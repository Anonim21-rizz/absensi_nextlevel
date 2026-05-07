from flask import Flask, redirect, url_for
from config import Config
from models import db
from models.user import User
from routes.auth import auth_bp, bcrypt
from routes.admin import admin_bp
from routes.attendance import attendance_bp
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Silakan login terlebih dahulu."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(attendance_bp)

    @app.route('/')
    def index():
        return redirect(url_for('attendance.scan'))

    # Create tables and initial admin if not exists
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(name='Administrator', email='admin@admin.com', password=hashed_password, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@admin.com / admin123")
            
        if not User.query.filter_by(role='user').first():
            hashed_password = bcrypt.generate_password_hash('user123').decode('utf-8')
            user1 = User(name='Siswa Pertama', email='siswa1@sekolah.com', password=hashed_password, role='user')
            user2 = User(name='Siswa Kedua', email='siswa2@sekolah.com', password=hashed_password, role='user')
            db.session.add_all([user1, user2])
            db.session.commit()
            print("Default users created: siswa1@sekolah.com / user123, siswa2@sekolah.com / user123")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
