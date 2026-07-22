from flask import Flask, redirect, render_template,request,url_for
from flask.globals import session
from flask_sqlalchemy import SQLAlchemy
import pymysql 
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user,login_manager,UserMixin,LoginManager,login_required,logout_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import current_user


localserver = True
app = Flask(__name__)
app.secret_key = '12345678'

login_manager=LoginManager(app)
login_manager.login_view='login'

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/socialmd')
db = SQLAlchemy(app)



app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@login_manager.user_loader
def load_user(user_id):
    return Signup.query.get(int(user_id))

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

class Signup(UserMixin,db.Model):
    user_id=db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(50))
    last_name=db.Column(db.String(50))
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(1000))
    phone=db.Column(db.Integer, unique=True)
    profileimg=db.Column(db.String(500))

    def get_id(self):
        return self.user_id
    
class Post(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    name = db.Column(db.String(100))
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    image = db.Column(db.String(500))
    date = db.Column(db.String(500))
    time = db.Column(db.String(500))
    likes = db.Column(db.Integer)

class Comments(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    comment= db.Column(db.String(500))
    commentedBy = db.Column(db.String(100))
    commentedOn = db.Column(db.String(100))

class Friends(db.Model):
    friends_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    requested_id = db.Column(db.Integer)
    isAccepted=db.Column(db.String(10))

class Contact(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    description = db.Column(db.String(500))

class Likes(db.Model):
    like_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, nullable=False)

# Create new tables (e.g. Likes) if they don't exist yet
with app.app_context():
    db.create_all()

def get_profile_img(user):
    """Return profile image filename or a default placeholder."""
    if user and user.profileimg:
        return user.profileimg
    return 'default_avatar.png'

@app.template_filter('timeago')
def timeago(date_str, time_str=None):
    try:
        if time_str:
            dt_str = f"{date_str} {time_str}".split('.')[0]
        else:
            dt_str = str(date_str).split('.')[0]
        post_time = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        diff = now - post_time
        seconds = diff.total_seconds()
        
        if seconds < 0:
            return "just now"
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds // 60)} minutes ago"
        elif seconds < 43200: # 12 hours
            return f"{int(seconds // 3600)} hours ago"
        else:
            # Over 12 hours, format as Month Day (e.g. Jan 11)
            formatted = post_time.strftime('%b %d')
            # Remove zero-padding on single digit days without relying on %-d (platform dependent)
            return formatted.replace(' 0', ' ')
    except Exception as e:
        return f"{date_str}"

@app.route("/")
def index():
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    page = request.args.get('page', 1, type=int)
    per_page = 5
    pagination = Post.query.order_by(Post.post_id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    data = pagination.items
    # Get set of post_ids the current user has already liked
    liked_post_ids = set(
        like.post_id for like in Likes.query.filter_by(user_id=current_user.user_id).all()
    )
    return render_template("index.html", data=data, pagination=pagination, liked_post_ids=liked_post_ids)

@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/contact/", methods=["GET", "POST"])
def contact():
    if request.method=="POST":
        email = request.form.get("email")
        desc = request.form.get("desc")
        query = Contact(email=email, description=desc)
        db.session.add(query)
        db.session.commit()
        flash("We Will get back to you soon...", "success")

    return render_template("contact.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))
        
    if request.method=="POST":
        firstName = request.form.get("fname", "").strip()
        lastName = request.form.get("lname", "").strip()
        email = request.form.get("email", "").strip()
        phoneNumber = request.form.get("phone", "").strip()
        password = request.form.get("pass1")
        confirmPassword = request.form.get("pass2")
        
        # Validations first! Return render_template to PRESERVE user input
        if password != confirmPassword:
            flash("Passwords do not match", "danger")
            return render_template("signup.html", fname=firstName, lname=lastName, email=email, phone=phoneNumber)
        
        if len(phoneNumber) < 10:
            flash("Please enter a valid phone number (at least 10 digits).", "danger")
            return render_template("signup.html", fname=firstName, lname=lastName, email=email, phone=phoneNumber)
            
        # DB Checks
        fetchemail = Signup.query.filter_by(email=email).first()
        fetchphone = Signup.query.filter_by(phone=phoneNumber).first()
        if fetchemail or fetchphone:
            flash("An account with this email or phone already exists.", "danger")
            return render_template("signup.html", fname=firstName, lname=lastName, email=email, phone=phoneNumber)
        
        gen_pass = generate_password_hash(password)
        new_user = Signup(
            first_name=firstName,
            last_name=lastName,
            email=email,
            password=gen_pass,
            phone=phoneNumber,
            profileimg="https://api.dicebear.com/7.x/avataaars/svg?seed=" + firstName
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Automatically log them in so they don't get confused by the login page
        login_user(new_user)
        flash("Account created successfully! You are now logged in.", "success")
        return redirect(url_for("index"))
        
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))
        
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pass1")
        user=Signup.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")
            return render_template("login.html")
        
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/test/")
def test():
    try:
        query = Test.query.all()
        print(query)
        sql_query="select * from test"
        with db.engine.begin() as conn:
            response=conn.exec_driver_sql(sql_query).all()
            print(response)
        return "Database is Connected"
    except Exception as e:
        return f"Database isn't Connected. Error: {e}"
    

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "POST":
        email = request.form['email']
        name = request.form['name']
        title = request.form['title']
        description = request.form['description']
        image_url = request.form.get('image_url', '').strip()

        date = datetime.now()
        datee = date.date()
        time = date.time()

        if not image_url:
            flash("Please provide an image URL.", "warning")
            return redirect(url_for("post"))

        new_post = Post(
            email=email,
            name=name,
            title=title,
            description=description,
            image=image_url,
            date=datee,
            time=time,
            likes=0
        )
        db.session.add(new_post)
        db.session.commit()
        
        flash("Post uploaded successfully!", "success")
        return redirect(url_for('index'))

    return render_template("posts.html")

@app.route("/like/<int:id>", methods=['GET', 'POST'])
@login_required
def like(id):
    # FIX: prevent duplicate likes
    already_liked = Likes.query.filter_by(user_id=current_user.user_id, post_id=id).first()
    if already_liked:
        flash("You already liked this post!", "info")
        return redirect(url_for("index"))
    post = Post.query.filter_by(post_id=id).first()
    if post:
        post.likes += 1
        db.session.add(Likes(user_id=current_user.user_id, post_id=id))
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/comment/<int:id>", methods=["GET", "POST"])
@login_required
def comment(id):
    if request.method == "POST":
        comment_text = request.form['comment']
        commentedBy = request.form['commented']
        commentedOn = datetime.now()
        query= Comments(post_id=id, comment=comment_text, commentedBy=commentedBy, commentedOn=commentedOn)
        db.session.add(query)
        db.session.commit()
        flash("Comment added successfully!", "success")
    return redirect(url_for("index"))

@app.route("/viewcomment/<int:id>",methods=["GET", "POST"])
def viewcomment(id):
    post = Comments.query.filter_by(post_id=id).all()
    return render_template("comments.html",  post=post)
    
@app.route("/connect",methods=["GET", "POST"])
@login_required
def connect():
    users=Signup.query.filter(Signup.user_id != current_user.user_id).all()
    # Build a dict of user_id -> friend status for current user
    friend_statuses = {}
    all_relations = Friends.query.filter(
        ((Friends.user_id == current_user.user_id) | (Friends.requested_id == current_user.user_id))
    ).all()
    for rel in all_relations:
        other_id = rel.requested_id if rel.user_id == current_user.user_id else rel.user_id
        if rel.isAccepted == 'True':
            friend_statuses[other_id] = 'friends'
        else:
            friend_statuses[other_id] = 'pending'
    return render_template("connect.html", users=users, friend_statuses=friend_statuses)

@app.route("/connectfriend/<int:friend_id>", methods=["GET"])
@login_required
def connectFriends(friend_id):
    # Check if a relation already exists between these two users in either direction
    existing = Friends.query.filter(
        ((Friends.user_id == current_user.user_id) & (Friends.requested_id == friend_id)) |
        ((Friends.user_id == friend_id) & (Friends.requested_id == current_user.user_id))
    ).first()
    if existing:
        flash("Friend request already sent or you are already friends.", "info")
        return redirect(url_for("connect"))
    new_request = Friends(user_id=current_user.user_id, requested_id=friend_id, isAccepted="False")
    db.session.add(new_request)
    db.session.commit()
    flash("Friend request sent!", "success")
    return redirect(url_for("connect"))

@app.route("/remove/<int:friend_id>", methods=["GET"])
@login_required
def remove(friend_id):
    relation = Friends.query.filter(
        ((Friends.user_id == current_user.user_id) & (Friends.requested_id == friend_id)) |
        ((Friends.user_id == friend_id) & (Friends.requested_id == current_user.user_id))
    ).first()
    if relation:
        db.session.delete(relation)
        db.session.commit()
        flash("Friend removed.", "success")
    return redirect(url_for("connect"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    userdata = Signup.query.filter_by(email=current_user.email).first()
    userdata.profileimg = get_profile_img(userdata)
    # Show RECEIVED friend requests (people who sent a request TO the current user) that are not yet accepted
    pending_requests = Friends.query.filter_by(requested_id=userdata.user_id, isAccepted="False").all()
    incoming_friends = []
    for req in pending_requests:
        sender = Signup.query.filter_by(user_id=req.user_id).first()
        if sender:
            sender.profileimg = get_profile_img(sender)
            incoming_friends.append(sender)

    getallmypost = Post.query.filter_by(email=userdata.email).order_by(Post.post_id.desc()).all()
    return render_template("profile.html", userdata=userdata, myids=incoming_friends, getallmypost=getallmypost)

@app.route("/editprofile/<int:id>", methods=["GET", "POST"])
@login_required
def editprofile(id):
    userdata=Signup.query.filter_by(user_id=id).first()
    userdata.profileimg = get_profile_img(userdata)
    return render_template("editprofile.html", userdata=userdata)
    
@app.route("/updateprofile/<int:id>", methods=["GET", "POST"])
@login_required
def updateprofile(id):
    userdata = Signup.query.filter_by(user_id=id).first()

    if request.method == "POST":
        firstName = request.form.get("fname")
        lastName = request.form.get("lname")
        email = request.form.get("email")
        phoneNumber = request.form.get("phone")
        profile_url = request.form.get('profile_url', '').strip()

        if len(phoneNumber) != 10:
            flash("Enter 10 digit Number.", "danger")
            return redirect(url_for("editprofile", id=id))

        userdata.first_name = firstName
        userdata.last_name = lastName
        userdata.email = email
        userdata.phone = phoneNumber

        if profile_url:
            userdata.profileimg = profile_url

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("editprofile.html", userdata=userdata)

@app.route("/deletepost/<int:id>", methods=["POST"])
@login_required
def deletepost(id):
    post = Post.query.filter_by(post_id=id).first()
    if not post:
        flash("Post not found.", "danger")
        return redirect(url_for("profile"))
    # Only the post owner can delete
    if post.email != current_user.email:
        flash("You are not authorized to delete this post.", "danger")
        return redirect(url_for("profile"))
    # Also delete associated comments and likes
    Comments.query.filter_by(post_id=id).delete()
    Likes.query.filter_by(post_id=id).delete()
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully.", "success")
    return redirect(url_for("profile"))

@app.route("/accept/<int:sender_id>", methods=["GET"])
@login_required
def acceptfriendrequest(sender_id):
    relation = Friends.query.filter_by(user_id=sender_id, requested_id=current_user.user_id).first()
    if relation:
        relation.isAccepted = 'True'
        db.session.commit()
        flash("Friend request accepted!", "success")
    else:
        flash("Friend request not found.", "danger")
    return redirect(url_for("profile"))

@app.route("/rejectrequest/<int:sender_id>", methods=["GET"])
@login_required
def rejectrequest(sender_id):
    relation = Friends.query.filter_by(user_id=sender_id, requested_id=current_user.user_id).first()
    if relation:
        db.session.delete(relation)
        db.session.commit()
        flash("Friend request rejected.", "info")
    return redirect(url_for("profile"))

@app.route("/search", methods=["GET"])
@login_required
def search():
    query = request.args.get('q', '').strip()
    user_results = []
    post_results = []
    if query:
        user_results = Signup.query.filter(
            (Signup.first_name.ilike(f'%{query}%')) |
            (Signup.last_name.ilike(f'%{query}%')) |
            (Signup.email.ilike(f'%{query}%'))
        ).filter(Signup.user_id != current_user.user_id).all()
        for u in user_results:
            u.profileimg = get_profile_img(u)

        post_results = Post.query.filter(
            (Post.title.ilike(f'%{query}%')) |
            (Post.description.ilike(f'%{query}%')) |
            (Post.name.ilike(f'%{query}%'))
        ).order_by(Post.post_id.desc()).all()
    return render_template("search.html", query=query, user_results=user_results, post_results=post_results)

if __name__ == '__main__':
    app.run(debug=True)
