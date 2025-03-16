from flask import Flask, render_template, url_for, request, redirect, flash, g, session, jsonify, Response
from datetime import datetime, timedelta
import os
import markdown
import yaml
import re
import sqlite3
import uuid
import hashlib
import secrets
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Use SECRET_KEY from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE = 'comments.sqlite'

# Admin credentials - change these to your own secure values
ADMIN_USERNAME = "sreekar_admin"  # Choose a username that's hard to guess
ADMIN_PASSWORD = "secure_password_change_me"  # IMPORTANT: Replace with a strong password

# Database functions
def get_db():
    """Connect to the comments database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection when the request ends."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """Query the database."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def prepare_comment_data(comment_row):
    """Convert SQLite.Row comment to dict with all required fields"""
    if not comment_row:
        return None
        
    # Convert to dict
    comment = dict(comment_row)
    
    # Add required fields with defaults
    if 'author_name' in comment and comment['author_name']:
        comment['author'] = comment['author_name']
    else:
        comment['author'] = 'Anonymous'
        
    # Format date
    if 'created_at' in comment and comment['created_at']:
        try:
            created_at = datetime.fromisoformat(comment['created_at'])
            comment['date'] = created_at.strftime("%B %d, %Y")
        except:
            comment['date'] = "Unknown date"
    else:
        comment['date'] = "Unknown date"
        
    return comment

def get_comments(post_id, status='approved'):
    """Get comments for a specific post in a threaded structure."""
    raw_comments = query_db(
        '''SELECT id, parent_id, author_name, content, created_at, author_token 
           FROM comments 
           WHERE post_id = ? AND status = ?
           ORDER BY created_at ASC''', 
        [post_id, status]
    )
    
    # Process each comment to ensure proper formatting
    comments = []
    for comment in raw_comments:
        comment_dict = prepare_comment_data(comment)
        if comment_dict:
            comments.append(comment_dict)
            
    return comments

def get_blog_posts():
    """Get all blog posts from the content/blog/posts directory."""
    posts = []
    posts_dir = os.path.join(os.path.dirname(__file__), 'content/blog/posts')
    
    # Create the directory if it doesn't exist
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)
        
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(posts_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    # Read the file content
                    content = file.read()
                    
                    # Extract front matter and content
                    if content.startswith('---'):
                        # Find the second '---' which marks the end of front matter
                        end_of_front_matter = content.find('---', 3)
                        if (end_of_front_matter != -1):
                            front_matter = content[3:end_of_front_matter].strip()
                            post_content = content[end_of_front_matter+3:].strip()
                            
                            try:
                                # Parse YAML front matter
                                metadata = yaml.safe_load(front_matter)
                                
                                # Handle case where yaml parsing succeeded but metadata is None
                                if metadata is None:
                                    metadata = {}
                                
                                # Convert markdown content to HTML
                                html_content = markdown.markdown(
                                    post_content,
                                    extensions=[
                                        'fenced_code', 
                                        'codehilite', 
                                        'tables', 
                                        'nl2br'  # This extension converts newlines to <br> tags
                                    ]
                                )
                                
                                # Get post ID from filename
                                post_id = os.path.splitext(filename)[0]
                                
                                # Create a summary from the content (first paragraph or first 150 chars)
                                summary = re.sub(r'<.*?>', '', html_content)  # Remove HTML tags
                                if len(summary) > 150:
                                    summary = summary[:150] + '...'
                                
                                # Create post object
                                post = {
                                    'id': post_id,
                                    'title': metadata.get('title', 'Untitled'),
                                    'date': metadata.get('date', ''),
                                    'author': metadata.get('author', 'Sreekar Reddy'),
                                    'summary': metadata.get('summary', summary),
                                    'content': html_content,
                                    'tags': metadata.get('tags', []),
                                    'excerpt': metadata.get('excerpt', summary[:100] + '...')
                                }
                                
                                posts.append(post)
                                
                            except yaml.YAMLError as e:
                                print(f"YAML parsing error in {filename}: {str(e)}")
                                # Try to manually fix the front matter
                                fixed_front_matter = fix_yaml_front_matter(front_matter)
                                try:
                                    metadata = yaml.safe_load(fixed_front_matter)
                                    # If successful, continue with the fixed metadata
                                    if metadata:
                                        html_content = markdown.markdown(post_content, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])
                                        post_id = os.path.splitext(filename)[0]
                                        summary = re.sub(r'<.*?>', '', html_content)
                                        if len(summary) > 150:
                                            summary = summary[:150] + '...'
                                            
                                        post = {
                                            'id': post_id,
                                            'title': metadata.get('title', 'Untitled'),
                                            'date': metadata.get('date', ''),
                                            'author': metadata.get('author', 'Sreekar Reddy'),
                                            'summary': metadata.get('summary', summary),
                                            'content': html_content,
                                            'tags': metadata.get('tags', []),
                                            'excerpt': metadata.get('excerpt', summary[:100] + '...')
                                        }
                                        
                                        posts.append(post)
                                except yaml.YAMLError:
                                    # If still failing, use default values
                                    print(f"Could not fix YAML in {filename}, using default values")
                                    post_id = os.path.splitext(filename)[0]
                                    html_content = markdown.markdown(post_content, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])
                                    summary = re.sub(r'<.*?>', '', html_content)[:150] + '...'
                                    
                                    post = {
                                        'id': post_id,
                                        'title': filename.replace('.md', '').replace('-', ' ').title(),
                                        'date': '',
                                        'author': 'Sreekar Reddy',
                                        'summary': summary,
                                        'content': html_content,
                                        'tags': [],
                                        'excerpt': summary[:100] + '...'
                                    }
                                    
                                    posts.append(post)
                        else:
                            print(f"Invalid front matter format in {filename}")
                    else:
                        print(f"No front matter found in {filename}")
            except Exception as e:
                print(f"Error processing file {filename}: {str(e)}")
    
    # Sort posts by date (newest first)
    try:
        posts.sort(key=lambda x: x['date'] if x['date'] else "1900-01-01", reverse=True)
    except Exception as e:
        print(f"Error sorting posts: {str(e)}")
    
    return posts

def fix_yaml_front_matter(front_matter):
    """Fix common YAML errors in front matter."""
    # Split into lines
    lines = front_matter.split('\n')
    fixed_lines = []
    
    for line in lines:
        if ':' in line:
            # Split by the first colon
            parts = line.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            
            # If the value contains another colon, wrap it in quotes
            if ':' in value and not (value.startswith('"') and value.endswith('"')):
                value = f'"{value.replace('"', '\\"')}"'
            
            fixed_lines.append(f"{key}: {value}")
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)  # Fixed: this line had syntax errors

# Add context processor to make current_year available in all templates
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/who-am-i")
def who_am_i():
    return render_template("who-am-i.html")

@app.route("/what-is-this")
def what_is_this():
    return render_template("what-is-this.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")

@app.route("/volunteering")
def volunteering():
    return render_template("volunteering.html")

# Blog routes
@app.route("/ufragments")
def blog_index():
    posts = get_blog_posts()
    return render_template("blog/index.html", posts=posts)

@app.route("/ufragments/<post_id>")
def blog_post(post_id):
    posts = get_blog_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if post is None:
        return "Post not found", 404
    
    # Ensure post has an author
    if 'author' not in post or not post['author']:
        post = dict(post)  # Convert to dict if needed
        post['author'] = 'Anonymous'
    
    # Get comments for this post
    comments = get_comments(post_id)
    
    return render_template("blog/post.html", post=post, comments=comments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Logged in successfully as admin')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('Logged out successfully')
    return redirect(url_for('home'))

@app.context_processor
def inject_admin_status():
    return {'is_admin': session.get('is_admin', False)}

# Comment management routes
@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment_inline(comment_id):
    # Allow both admin and comment author to delete
    is_admin = session.get('is_admin', False)
    comment_token = request.cookies.get('comment_token')
    
    # Get the comment
    comment = query_db('SELECT * FROM comments WHERE id = ?', [comment_id], one=True)
    if not comment:
        flash('Comment not found')
        return redirect(request.referrer or url_for('home'))
    
    # Check permissions
    can_delete = is_admin
    if comment_token and comment.get('author_token') == comment_token:
        # Check if within edit window (24 hours)
        comment_time = datetime.fromisoformat(comment['created_at'])
        now = datetime.now()
        if (now - comment_time) < timedelta(hours=24):
            can_delete = True
    
    if not can_delete:
        flash('Permission denied')
        return redirect(request.referrer or url_for('home'))
    
    # Delete the comment
    db = get_db()
    db.execute('DELETE FROM comments WHERE id = ?', [comment_id])
    db.commit()
    
    flash('Comment deleted')
    return redirect(request.referrer or url_for('home'))

@app.route('/comment/<int:comment_id>/edit', methods=['POST'])
def edit_comment(comment_id):
    # Only comment author can edit
    comment_token = request.cookies.get('comment_token')
    new_content = request.form.get('content', '').strip()
    
    # Validate
    if not new_content:
        flash('Comment cannot be empty')
        return redirect(request.referrer or url_for('home'))
    
    # Get the comment
    comment = query_db('SELECT * FROM comments WHERE id = ?', [comment_id], one=True)
    if not comment:
        flash('Comment not found')
        return redirect(request.referrer or url_for('home'))
    
    # Check permissions
    can_edit = False
    if comment_token and comment.get('author_token') == comment_token:
        # Check if within edit window (24 hours)
        comment_time = datetime.fromisoformat(comment['created_at'])
        now = datetime.now()
        if (now - comment_time) < timedelta(hours=24):
            can_edit = True
    
    if not can_edit:
        flash('Permission denied or edit window expired (24 hours)')
        return redirect(request.referrer or url_for('home'))
    
    # Update the comment
    db = get_db()
    db.execute('UPDATE comments SET content = ? WHERE id = ?', [new_content, comment_id])
    db.commit()
    
    flash('Comment updated')
    return redirect(request.referrer or url_for('home'))

@app.route("/ufragments/<post_id>/comment", methods=['POST'])
def add_comment(post_id):
    # Check if post exists
    posts = get_blog_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        return "Post not found", 404
        
    # Get form data
    author_name = request.form.get('author_name', '').strip()
    author_email = request.form.get('author_email', '').strip()
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', None)
    
    # Validate data
    if not all([author_name, content]):
        flash('Name and comment are required.')
        return redirect(url_for('blog_post', post_id=post_id))
    
    # Generate a token for this commenter
    comment_token = request.cookies.get('comment_token')
    if not comment_token:
        comment_token = secrets.token_hex(16)
    
    # Validate parent_id if provided
    if parent_id:
        try:
            parent_id = int(parent_id)
            # Verify this parent exists and belongs to this post
            parent = query_db('SELECT id FROM comments WHERE id = ? AND post_id = ?', 
                            [parent_id, post_id], one=True)
            if not parent:
                parent_id = None
        except (ValueError, TypeError):
            parent_id = None
    
    # Insert comment into database
    db = get_db()
    db.execute(
        'INSERT INTO comments (post_id, parent_id, author_name, author_email, content, author_token, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [post_id, parent_id, author_name, author_email, content, comment_token, datetime.now().isoformat(), 'pending']
    )
    db.commit()
    
    # Set a cookie so the user can edit/delete this comment later
    response = redirect(url_for('blog_post', post_id=post_id))
    response.set_cookie('comment_token', comment_token, max_age=30*24*60*60)  # 30 days
    flash('Your comment has been submitted and is awaiting approval.')
    return response

# Simple admin routes for comment management
@app.route("/admin/comments")
def admin_comments():
    # In a real app, you'd add authentication here
    pending_comments = query_db('SELECT * FROM comments WHERE status = ? ORDER BY created_at DESC', ['pending'])
    approved_comments = query_db('SELECT * FROM comments WHERE status = ? ORDER BY created_at DESC', ['approved'])
    
    return render_template("admin/comments.html", pending=pending_comments, approved=approved_comments)

@app.route("/admin/comments/<int:comment_id>/approve", methods=['POST'])
def approve_comment(comment_id):
    # In a real app, you'd add authentication here
    db = get_db()
    db.execute('UPDATE comments SET status = ? WHERE id = ?', ['approved', comment_id])
    db.commit()
    
    flash('Comment approved.')
    return redirect(url_for('admin_comments'))

@app.route("/admin/comments/<int:comment_id>/delete", methods=['POST'])
def delete_comment(comment_id):
    # In a real app, you'd add authentication here
    db = get_db()
    db.execute('DELETE FROM comments WHERE id = ?', [comment_id])
    db.commit()
    
    flash('Comment deleted.')
    return redirect(url_for('admin_comments'))

# Dynamic CSS generation for animations
@app.route('/dynamic/animations.css')
def dynamic_animations():
    """Generate animations dynamically to reduce CSS clutter"""
    
    # Generate particle animations
    particles = []
    for i in range(12):
        x1 = random.randint(-100, 100)
        y1 = random.randint(-100, 100)
        x2 = random.randint(-100, 100) 
        y2 = random.randint(-100, 100)
        x3 = random.randint(-100, 100)
        y3 = random.randint(-100, 100)
        delay = random.uniform(0, 5)
        duration = random.uniform(15, 30)
        opacity_start = random.uniform(0.3, 0.7)
        opacity_mid = random.uniform(0.5, 0.9)
        opacity_end = random.uniform(0.2, 0.6)
        
        particles.append({
            'index': i,
            'x1': x1, 'y1': y1,
            'x2': x2, 'y2': y2, 
            'x3': x3, 'y3': y3,
            'delay': delay,
            'duration': duration,
            'opacity_start': opacity_start,
            'opacity_mid': opacity_mid,
            'opacity_end': opacity_end
        })
    
    # Generate pulse effect variations
    pulses = []
    for i in range(5):
        duration = random.uniform(2, 5)
        scale_start = 1
        scale_mid = random.uniform(1.1, 1.5)
        scale_end = random.uniform(0.85, 0.95)
        delay = random.uniform(0, 2)
        
        pulses.append({
            'index': i,
            'duration': duration,
            'scale_start': scale_start,
            'scale_mid': scale_mid,
            'scale_end': scale_end,
            'delay': delay
        })
        
    # Generate shine effects
    shines = []
    for i in range(3):
        duration = random.uniform(3, 8)
        delay = random.uniform(0, 3)
        angle = random.randint(30, 60)
        
        shines.append({
            'index': i,
            'duration': duration,
            'delay': delay,
            'angle': angle
        })
    
    # Render the template with our animation data
    css = render_template('dynamic/animations.css', 
                          particles=particles, 
                          pulses=pulses,
                          shines=shines)
    
    return Response(css, mimetype='text/css')

# Add context processor for animation utility functions
@app.context_processor
def utility_processor():
    """Utility functions for templates"""
    def attach_random_animation_class(base_class, count=5):
        """Generate a random animation class for visual variety"""
        animation_type = random.choice(['pulse', 'particle', 'shine'])
        animation_index = random.randint(0, count-1)
        return f"{base_class} {animation_type}-{animation_index}"
        
    return dict(
        attach_random_animation_class=attach_random_animation_class
    )

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
