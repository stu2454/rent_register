from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from .extensions import db
from .models import User

auth_bp = Blueprint('auth', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password are required.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash(f"Username '{username}' already exists.", 'danger')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f"User '{username}' created.", 'success')
        return redirect(url_for('auth.users'))
    all_users = User.query.order_by(User.username).all()
    return render_template('auth/users.html', users=all_users)


@auth_bp.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
def delete_user(uid):
    from flask_login import current_user
    if uid == current_user.id:
        flash("You can't delete your own account.", 'danger')
        return redirect(url_for('auth.users'))
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", 'success')
    return redirect(url_for('auth.users'))
