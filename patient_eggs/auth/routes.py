from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from patient_eggs import db
from patient_eggs.models import User
from urllib.parse import urlparse
import os

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check for Environment Admin Login
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_pass = os.environ.get('ADMIN_PASSWORD')
        
        if admin_email and admin_pass and email == admin_email and password == admin_pass:
            # Login as virtual admin
            user = User(
                id=0, 
                username=os.environ.get('ADMIN_USERNAME', 'SuperAdmin'), 
                email=admin_email, 
                is_admin=True
            )
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.home')
            return redirect(next_page)

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.home')
            return redirect(next_page)
        flash('Invalid email or password')
        
    return render_template('login.html')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')
