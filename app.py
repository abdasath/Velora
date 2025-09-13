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

app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:@localhost/socialmd'
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

@app.route("/")
def index():
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    data= Post.query.all()
    return render_template("index.html", data=data)

@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/contact/", methods=["GET", "POST"])
def contact():
    if request.method=="POST":
        email = request.form.get("email")
        email = request.form.get("email")
        desc = request.form.get("desc")
        query = Contact(email=email, description=desc)
        db.session.add(query)
        db.session.commit()
        flash("We Will get back to you soon...", "success")

    return render_template("contact.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method=="POST":
        firstName = request.form.get("fname")
        lastName = request.form.get("lname")
        email = request.form.get("email")
        phoneNumber = request.form.get("phone")
        password = request.form.get("pass1")
        confirmPassword = request.form.get("pass2")
        print(firstName, lastName, email, phoneNumber, password, confirmPassword)
        if password != confirmPassword:
            flash("Passwords do not match", "danger")
            return redirect(url_for("signup"))
        
        fetchemail = Signup.query.filter_by(email=email).first()
        fetchphone = Signup.query.filter_by(phone=phoneNumber).first()
        if fetchemail or fetchphone:
            flash("An account with this user already exists.", "danger")
            return redirect(url_for("signup"))
        
        if len(phoneNumber) != 10:
            flash("Enter 10 digit Number.", "danger")
            return redirect(url_for("signup"))
        
        gen_pass=generate_password_hash(password)
        
        query = f"""
         INSERT INTO signup (first_name, last_name, email, password, phone)
         VALUES ('{firstName}', '{lastName}', '{email}', '{gen_pass}', '{phoneNumber}')
         """

        with db.engine.begin() as conn:
            conn.exec_driver_sql(query)
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pass1")
        user=Signup.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return render_template("index.html")
        else:
            flash("Invalid email or password", "danger")
            return render_template("login.html")
        
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

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

def post():
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    if request.method == "POST":
        email = request.form['email']
        name = request.form['name']
        title = request.form['title']
        description = request.form['description']
        file = request.files['image']
        date= datetime.now()
        datee=date.date()
        time=date.time()

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            query=Post(email=email,name=name, title=title, description=description, image=file.filename ,date=datee, time=time, likes=0)
            db.session.add(query)
            db.session.commit()
            flash("Post created successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid file type. Only images are allowed.", "warning")
            return redirect(url_for("post"))
        

    return render_template("posts.html")

@app.route("/like/<int:id>",methods=['GET','POST'])
def like(id):
    post = Post.query.filter_by(post_id=id).first()
    post.likes += 1
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/comment/<int:id>", methods=["GET", "POST"])
def comment(id):
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    if request.method == "POST":
        comment = request.form['comment']
        commentedBy = request.form['commented']
        commentedOn = datetime.now()
        query= Comments(post_id=id, comment=comment, commentedBy=commentedBy, commentedOn=commentedOn)
        db.session.add(query)
        db.session.commit()
        flash("Comment added successfully!", "success")
        return redirect(url_for("index"))
    
@app.route("/viewcomment/<int:id>",methods=["GET", "POST"])
def viewcomment(id):
    post = Comments.query.filter_by(post_id=id).all()
    return render_template("comments.html",  post=post)
    
@app.route("/connect",methods=["GET", "POST"])
def connect():
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    users=Signup.query.filter(Signup.user_id != current_user.user_id).all() #    users=Signup.query.all()
    return render_template("connect.html",users=users)

@app.route("/connectfriend/<path:ids>",methods=["GET"])
def connectFriends(ids):
    print(ids)
    data= ids.split("/")
    print(data)
    users=Signup.query.all()
    d1=Friends.query.filter_by(user_id=data[1]).first()
    d2=Friends.query.filter_by(requested_id=data[0]).first()
    if d1 and d2:
        flash("Already sent","primary")
        return render_template("connect.html",users=users)
    query=Friends(user_id=data[1], requested_id=data[0], isAccepted="False")
    db.session.add(query)
    db.session.commit()
    flash(f"Friend request sent", "success")
    return render_template("connect.html", users=users)

@app.route("/remove/<path:ids>",methods=["GET"])
def remove(ids):
    data= ids.split("/")
    print(data)
    users=Signup.query.all()
    d1=Friends.query.filter_by(user_id=data[1]).first()
    d2=Friends.query.filter_by(requested_id=data[0]).first()
    if d1 and d2:
        #query = f"DELETE FROM friends WHERE user_id={data[1]} AND requested_id={data[0]}"

        query=f"Delete from `friends` where `friends`.`user_id`={data[1]} and `friends`.`requested_id`={data[0]}"
        with db.engine.begin() as conn:
            conn.exec_driver_sql(query)
            flash("Request Cancelled", "success")
            return render_template("connect.html",users=users)
    
    return render_template("connect.html",users=users)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    
    userdata = Signup.query.filter_by(email=current_user.email).first()
    friends=Friends.query.filter_by(user_id=userdata.user_id).all()
    getallmypost=Post.query.filter_by(email=userdata.email).all()
    myids=[]
    for i in friends:
        signupdata=Signup.query.filter_by(user_id=i.requested_id).first()
        myids.append(signupdata)

    return render_template("profile.html", userdata=userdata,myids=myids,getallmypost=getallmypost)

@app.route("/editprofile/<int:id>", methods=["GET", "POST"])
def editprofile(id):
    if not current_user.is_authenticated:
        flash("Please login to view posts", "warning")
        return redirect(url_for("login"))
    userdata=Signup.query.filter_by(user_id=id).first()
    print(userdata,"data")
    return render_template("editprofile.html", userdata=userdata)
    
@app.route("/updateprofile/<int:id>", methods=["GET", "POST"])
def updateprofile(id):
    userdata = Signup.query.filter_by(email=current_user.email,user_id=id).first() #user_id=id

    if request.method == "POST":
        firstName = request.form.get("fname")
        lastName = request.form.get("lname")
        email = request.form.get("email")
        phoneNumber = request.form.get("phone")
        file = request.files['profileimage']

        if len(phoneNumber) != 10:
            flash("Enter 10 digit Number.", "danger")
            return redirect(url_for("editprofile", id=id)) #edit id=id

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            query = f"UPDATE `signup` SET `first_name` = '{firstName}', `last_name` = '{lastName}',`email` = '{email}',`phone` = '{phoneNumber}',`profileimg` = '{filename}' WHERE `signup`.`user_id` = {id}"
        
            with db.engine.begin() as conn:
             conn.exec_driver_sql(query)
             flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))
    
        else:
            query1 = f"UPDATE `signup`SET `first_name` = '{firstName}',`last_name` = '{lastName}',`email` = '{email}',`phone` = '{phoneNumber}'WHERE `signup`.`user_id` = {id}"

            with db.engine.begin() as conn:
             conn.exec_driver_sql(query1)
             flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))


    return render_template("profile.html", userdata=userdata)

@app.route("/accept/<int:requested_id>/<int:user_id>", methods=["GET"])
def acceptfriendrequest(requested_id, user_id):
    query = f"""
        UPDATE friends
        SET isAccepted = 'True'
        WHERE requested_id = {requested_id} AND user_id = {user_id}
    """
    with db.engine.begin() as conn:
        conn.exec_driver_sql(query)
        flash("Friend request accepted", "success")
    return redirect(url_for("profile"))

app.run(debug=True)