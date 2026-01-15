from flask import render_template, url_for, flash, redirect, request, Blueprint, abort
from flask_login import login_user, current_user, logout_user, login_required
from . import db, bcrypt
from .models import User, Post, Comment, Like, Notification
from sqlalchemy import func
from .ai_helper import continue_story, generate_story_starter, suggest_titles, improve_writing, get_writing_suggestions

main = Blueprint('main', __name__)

# Helper: pagination
def paginate(query, page, per_page=5):
    total = query.count()
    items = query.offset((page-1)*per_page).limit(per_page).all()
    pages = (total + per_page - 1)//per_page
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < pages else None
    }

# Home / Posts feed
@main.route('/')
@main.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    q = Post.query.order_by(Post.date_posted.desc())
    p = paginate(q, page, per_page=5)
    return render_template('index.html', posts=p['items'], p=p)

@main.route('/posts')
def posts():
    page = request.args.get('page', 1, type=int)
    q = Post.query.order_by(Post.date_posted.desc())
    p = paginate(q, page, per_page=5)
    return render_template('index.html', posts=p['items'], p=p)

# User profile
@main.route('/profile/<username>')
def profile(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first_or_404()
    page = request.args.get('page', 1, type=int)
    q = Post.query.filter_by(author=user).order_by(Post.date_posted.desc())
    p = paginate(q, page, per_page=5)
    return render_template('profile.html', user=user, posts=p['items'], p=p)

# Edit profile
@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        current_user.bio = bio
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile', username=current_user.username))
    return render_template('edit_profile.html')

# Register
@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('main.register'))
        # Case-insensitive uniqueness check
        if User.query.filter(func.lower(User.username) == username.lower()).first():
            flash('Username already taken. Please choose another.', 'warning')
            return redirect(url_for('main.register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

# Login
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        # Case-insensitive user lookup
        user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login failed. Check username and password.', 'danger')
    return render_template('login.html')

# Logout
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.home'))

# Dashboard
@main.route('/dashboard')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    q = Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc())
    p = paginate(q, page, per_page=5)
    return render_template('dashboard.html', my_posts=p['items'], p=p, username=current_user.username)

# Create post
@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        category = request.form.get('category')

        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('main.new_post'))

        post = Post(
            title=title,
            content=content,
            category=category,
            author=current_user
        )

        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        
        # Notify all followers about the new post
        followers = current_user.followers.all()
        for follower in followers:
            Notification.create_notification(
                user_id=follower.id,
                sender_id=current_user.id,
                notification_type='new_post',
                message=f'{current_user.username} published a new story "{title}"',
                link=url_for('main.post_detail', post_id=post.id)
            )
        return redirect(url_for('main.post_detail', post_id=post.id))

    return render_template('new_post.html')

# Edit post (owner only)
@main.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('main.edit_post', post_id=post.id))
        post.title = title
        post.content = content
        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('main.post_detail', post_id=post.id))
    return render_template('edit_post.html', post=post)

# Delete post (owner only)
@main.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    # Safety: manual cascade for legacy DBs
    Comment.query.filter_by(post_id=post.id).delete(synchronize_session=False)

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('main.dashboard'))

# Post detail + comments + view count
@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    # Fix NoneType error for views count
    if post.views is None:
        post.views = 0
    post.views += 1
    db.session.commit()

    # Handle new comment
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please log in to comment.', 'info')
            return redirect(url_for('main.login', next=url_for('main.post_detail', post_id=post.id)))
        content = request.form.get('comment_content', '').strip()
        if not content:
            flash('Comment cannot be empty.', 'warning')
            return redirect(url_for('main.post_detail', post_id=post.id))
        comment = Comment(content=content, commenter=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added.', 'success')
        
        # Create notification for post author (don't notify self)
        if post.author.id != current_user.id:
            Notification.create_notification(
                user_id=post.author.id,
                sender_id=current_user.id,
                notification_type='comment',
                message=f'{current_user.username} commented on your story "{post.title}"',
                link=url_for('main.post_detail', post_id=post.id)
            )
        return redirect(url_for('main.post_detail', post_id=post.id))

    comments = Comment.query.filter_by(post=post).order_by(Comment.date_commented.desc()).all()
    return render_template('post_detail.html', post=post, comments=comments)

@main.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Ensure likes is not None
    if post.likes is None:
        post.likes = 0
    # Check if user already liked
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing_like:
        flash('You have already liked this post.', 'warning')
    else:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        post.likes += 1
        db.session.commit()
        flash('You liked this post!', 'success')
        
        # Create notification for post author (don't notify self)
        if post.author.id != current_user.id:
            Notification.create_notification(
                user_id=post.author.id,
                sender_id=current_user.id,
                notification_type='like',
                message=f'{current_user.username} liked your story "{post.title}"',
                link=url_for('main.post_detail', post_id=post.id)
            )
    return redirect(request.referrer or url_for('main.home'))

@main.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.home'))
    if user == current_user:
        flash('You cannot follow yourself!', 'warning')
        return redirect(url_for('main.profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {user.username}!', 'success')
    
    # Create notification for the followed user
    Notification.create_notification(
        user_id=user.id,
        sender_id=current_user.id,
        notification_type='follow',
        message=f'{current_user.username} started following you',
        link=url_for('main.profile', username=current_user.username)
    )
    return redirect(url_for('main.profile', username=username))

@main.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.home'))
    if user == current_user:
        flash('You cannot unfollow yourself!', 'warning')
        return redirect(url_for('main.profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have unfollowed {user.username}.', 'info')
    return redirect(url_for('main.profile', username=username))

@main.route('/feed')
@login_required
def feed():
    page = request.args.get('page', 1, type=int)
    q = current_user.followed_posts()
    p = paginate(q, page, per_page=5)
    return render_template('feed.html', posts=p['items'], p=p)

@main.route('/profile/<username>/followers')
def followers_list(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first_or_404()
    page = request.args.get('page', 1, type=int)
    followers_pagination = user.followers.paginate(page=page, per_page=20, error_out=False)
    return render_template('followers.html', user=user, users=followers_pagination.items, pagination=followers_pagination)

@main.route('/profile/<username>/following')
def following_list(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first_or_404()
    page = request.args.get('page', 1, type=int)
    following_pagination = user.followed.paginate(page=page, per_page=20, error_out=False)
    return render_template('following.html', user=user, users=following_pagination.items, pagination=following_pagination)

@main.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    q = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc())
    p = paginate(q, page, per_page=10)
    return render_template('notifications.html', notifications=p['items'], p=p)

@main.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    current_user.mark_notifications_read()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('main.notifications'))

@main.route('/notifications/mark-one-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_one_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.is_read = True
    db.session.commit()
    if notification.link:
        return redirect(notification.link)
    return redirect(url_for('main.notifications'))

@main.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    db.session.delete(notification)
    db.session.commit()
    flash('Notification deleted.', 'success')
    return redirect(url_for('main.notifications'))

@main.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
    db.session.commit()
    flash('All notifications cleared.', 'success')
    return redirect(url_for('main.notifications'))

# ============== AI WRITING ASSISTANT ROUTES ==============

@main.route('/ai-assistant')
@login_required
def ai_assistant():
    """AI Writing Assistant page."""
    return render_template('ai_assistant.html')

@main.route('/api/ai/continue-story', methods=['POST'])
@login_required
def api_continue_story():
    """API endpoint to continue a story."""
    data = request.get_json()
    content = data.get('content', '')
    genre = data.get('genre', 'general')
    words = data.get('words', 150)
    
    if not content:
        return {'success': False, 'error': 'No content provided'}, 400
    
    result = continue_story(content, genre, words)
    return result

@main.route('/api/ai/generate-starter', methods=['POST'])
@login_required
def api_generate_starter():
    """API endpoint to generate a story starter."""
    data = request.get_json()
    genre = data.get('genre', 'general')
    theme = data.get('theme', '')
    words = data.get('words', 200)
    
    result = generate_story_starter(genre, theme, words)
    return result

@main.route('/api/ai/suggest-titles', methods=['POST'])
@login_required
def api_suggest_titles():
    """API endpoint to suggest titles."""
    data = request.get_json()
    content = data.get('content', '')
    count = data.get('count', 5)
    
    if not content:
        return {'success': False, 'error': 'No content provided'}, 400
    
    result = suggest_titles(content, count)
    return result

@main.route('/api/ai/improve-writing', methods=['POST'])
@login_required
def api_improve_writing():
    """API endpoint to improve writing."""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return {'success': False, 'error': 'No text provided'}, 400
    
    result = improve_writing(text)
    return result

@main.route('/api/ai/get-suggestions', methods=['POST'])
@login_required
def api_get_suggestions():
    """API endpoint to get writing suggestions."""
    data = request.get_json()
    content = data.get('content', '')
    
    if not content:
        return {'success': False, 'error': 'No content provided'}, 400
    
    result = get_writing_suggestions(content)
    return result