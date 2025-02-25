from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from models import db, Post, Comment, User, Follow, Like

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hultagram.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = "supersecretkey"

db.init_app(app)

# ---------------------- Initialize Flask-Login ----------------------
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------- Initialize the Database ----------------------
with app.app_context():
    db.create_all()

# ---------------------- Routes ----------------------

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        caption = request.form['caption']
        new_post = Post(user_id=current_user.id, image_filename=filename, caption=caption)
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('index'))
    
    return render_template('create.html')

# ---------------------- Like System (Prevent Multiple Likes) ----------------------

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if the user already liked the post
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing_like:
        db.session.delete(existing_like)  # Unlike if already liked
    else:
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)

    db.session.commit()
    return redirect(url_for('index'))

# ---------------------- Post Detail & Comments ----------------------

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)


    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.asc()).all()


    liked_users = {like.user_id for like in post.likes}


    followed_users = {follow.followed_id for follow in current_user.following} if current_user.is_authenticated else set()

    return render_template('post_detail.html', post=post, comments=comments, liked_users=liked_users, followed_users=followed_users)

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)

    content = request.form.get('content')
    if not content:
        flash("Comment cannot be empty!", "danger")
        return redirect(url_for('post_detail', post_id=post_id))

    comment = Comment(post_id=post_id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()

    flash("Comment added successfully!", "success")
    return redirect(url_for('post_detail', post_id=post_id))


# ---------------------- User Authentication ----------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))  # Redirect to home instead of login

# ---------------------- User Profile & Follow System ----------------------

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    followed_users = user.get_followed_users()
    return render_template('profile.html', user=user, followed_users=followed_users)

@app.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return "You cannot follow yourself", 400

    if not current_user.is_following(user):
        follow = Follow(follower_id=current_user.id, followed_id=user.id)
        db.session.add(follow)
        db.session.commit()
    
    return redirect(url_for('profile', username=user.username))

@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user.id).first()

    if follow:
        db.session.delete(follow)
        db.session.commit()

    return redirect(url_for('profile', username=user.username))

# ---------------------- Search Functionality ----------------------

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    results = User.query.filter(User.username.contains(query)).all()
    return render_template('search.html', results=results)

# ---------------------- Edit Post ----------------------

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        post.caption = request.form['caption']
        db.session.commit()
        return redirect(url_for('profile', username=current_user.username))

    return render_template('edit_post.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)
