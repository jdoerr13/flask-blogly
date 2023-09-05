"""Blogly application."""

from flask import Flask, request, redirect, render_template, flash
from models import db, connect_db, User, Post, Tag
from flask_debugtoolbar import DebugToolbarExtension
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///blogly'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "chickenzarecool21837"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
# app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True
toolbar = DebugToolbarExtension(app)

# #pass in app from models.py
connect_db(app)

app.app_context().push()
db.create_all()


@app.route('/')
def root():
    """Homepage redirects to list of users."""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    print(posts)
    # return redirect("/users")
    return render_template('homepage.html', posts=posts)


@app.route('/users')
def users_index():
    """Show a page with info on all users"""

    users = User.query.order_by(User.last_name, User.first_name).all()
    print(users)
    return render_template('index.html', users=users)


@app.route('/users/new', methods=["GET"])
def users_new_form():
    """Show a form to create a new user"""
    print("Entering users_new_form")
    return render_template('new.html')


@app.route("/users/new", methods=["POST"])
def users_new():
    """Handle form submission for creating a new user"""
    print("Entering users_new")
    new_user = User(
        first_name=request.form['first_name'],
        last_name=request.form['last_name'],
        image_url=request.form['image_url'] or None)

    db.session.add(new_user)
    db.session.commit()

    print("New user added:", new_user)

    return redirect("/users")

@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show a page with info on a specific user"""
    print("Inside users_show")
    user = User.query.get_or_404(user_id)
    print(user)

    posts= Post.query.filter_by(user_id=user.id)
    
    return render_template('show.html', user=user, posts=posts)

@app.route('/users/<int:user_id>/edit', methods=["GET"])
def users_edit_form(user_id):
    """Show a form to edit a user's information"""
    
    user = User.query.get_or_404(user_id)
    return render_template('edit.html', user=user)

@app.route('/users/<int:user_id>/edit', methods=["POST"])
def users_edit(user_id):
    """Process the edit form and update a user's information"""
    
    user = User.query.get_or_404(user_id)
    user.first_name = request.form['first_name']
    user.last_name = request.form['last_name']
    user.image_url = request.form['image_url']
    
    db.session.add(user)
    db.session.commit()

    return redirect("/users")

@app.route('/users/<int:user_id>/delete', methods=["POST"])
def users_delete(user_id):
    """Handle form submission for deleting a user and their posts"""

    user = User.query.get_or_404(user_id)
# Get or create a default user #CHATGPT HELPED ME WITH THIS CODE BECAUSE I KEPT GETTING THIS ERROR: IntegrityError
# sqlalchemy.exc.IntegrityError: (psycopg2.errors.NotNullViolation) null value in column "user_id" of relation "posts" violates not-null constraint
# DETAIL:  Failing row contains (21, dfd, dfdf, 2023-09-03 17:03:42.140448, null).
    default_user = User.query.filter_by(first_name="Default", last_name="User").first()
    if default_user is None:
        default_user = User(first_name="Default", last_name="User", image_url="default_image_url")
        db.session.add(default_user)
        db.session.commit()

    # Update the user_id in posts associated with the user
    Post.query.filter_by(user_id=user_id).update({'user_id': default_user.id})

    # Then, delete the user
    db.session.delete(user)
    db.session.commit()

    flash(f"User '{user.full_name}' and associated posts deleted.")

    return redirect('/users')

#______________________________________
#FROM THE SHOW.HTML(shows the specific users info) PAGE- THEN CLICK ON ADD POST LINK AT BOTTON TO NEW_POST.HTML
@app.route('/users/<int:user_id>/posts/new', methods=["GET"]) #THIS LINK IS THE BOTTOM OF SHOW.HTML
def posts_new_form(user_id):
    """Show a form to create a new post for a specific user"""
    #queries the database for a user with the specified user_id
    user = User.query.get_or_404(user_id)
    print("Inside posts_new_form")
    print("User:", user)  # Print user information for debugging
    tags = Tag.query.all()
    return render_template('new_post.html', user=user, tags=tags)

@app.route('/users/<int:user_id>/posts/new', methods=["POST"])
def posts_new(user_id):
    """Handle form submission for creating a new post for a specific user"""
    #queries the database for a user with the specified user_id
    user = User.query.get_or_404(user_id)
    tag_ids = [int(num) for num in request.form.getlist("tags")]
    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
    # print("Form Data:")
    # print("Title:", request.form['title'])
    # print("Content:", request.form['content'])

    new_post = Post(title=request.form['title'],
                    content=request.form['content'],
                    created_at=datetime.now(),
                    user_id=user.id,
                    tags=tags)

    db.session.add(new_post)
    db.session.commit()
    flash(f"Post '{new_post.title}' added.")

    return redirect(f"/users/{user_id}")

#STARTS HERE- SHOWS A SPECIFIC USER AFTER YOU CLICK ON ONE AFTER 'USERS'NAV BAR (INDEX.HTML) THEN TO HOMEPAGE.HTML
@app.route('/posts/<int:post_id>')
def posts_show(post_id):
    """Show a page with info on a specific post"""
    post = Post.query.get_or_404(post_id)
    tags = post.tags.all()
    return render_template('show.html', post=post, tags=tags)



#clicking on EDIT BUTTON FROM THE SHOW PAGE
@app.route('/users/<int:user_id>/edit_post/<int:post_id>', methods=["GET"])
def posts_edit(user_id, post_id):
    """Show a form to edit an existing post"""
    user = User.query.get(user_id)
    post = Post.query.get_or_404(post_id)
    tags= Tag.query.all()
    return render_template('edit_post.html', user=user, post=post, tags=tags)

@app.route('/users/<int:user_id>/edit_post/<int:post_id>', methods=["POST"])
def posts_update(post_id):
    """Handle form submission for updating an existing post"""

    post = Post.query.get_or_404(post_id)
    post.title = request.form['title']
    post.content = request.form['content']

    tag_ids = [int(num) for num in request.form.getlist("tags")]
    post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    db.session.add(post)
    db.session.commit()
    flash(f"Post '{post.title}' edited.")

    return redirect(f"/users/{post.user_id}")


@app.route('/users/<int:user_id>/posts/<int:post_id>/delete', methods=["POST"])
def posts_destroy(user_id, post_id):
    """Handle form submission for deleting an existing post"""

    post = Post.query.get_or_404(post_id)
    post.user_id = None
    db.session.delete(post)
    db.session.commit()
    flash(f"Post '{post.title} deleted.")

    return redirect(f"/users/{user_id}")

#________________________________________________________________________________________________
@app.route('/tags')
def tags_index():
    """Show a page with info on all tags"""

    tags = Tag.query.all()
    return render_template('index_tags.html', tags=tags)


@app.route('/tags/new')
def tags_new_form():
    """Show a form to create a new tag"""

    posts = Post.query.all()
    return render_template('new_tags.html', posts=posts)

@app.route("/tags/new", methods=["POST"])
def tags_new():
    """Handle form submission for creating a new tag"""

    post_ids = [int(num) for num in request.form.getlist("posts")]
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    new_tag = Tag(name=request.form['name'], posts=posts)

    db.session.add(new_tag)
    db.session.commit()
    flash(f"Tag '{new_tag.name}' added.")

    return redirect("/tags")

@app.route('/tags/<int:tag_id>')
def tags_show(tag_id):
    """Show a page with info on a specific tag"""

    tag = Tag.query.get_or_404(tag_id)
    return render_template('show_tags.html', tag=tag)

@app.route('/tags/<int:tag_id>/edit')
def tags_edit_form(tag_id):
    """Show a form to edit an existing tag"""

    tag = Tag.query.get_or_404(tag_id)
    posts = Post.query.all()
    return render_template('edit_tags.html', tag=tag, posts=posts)

@app.route('/tags/<int:tag_id>/edit', methods=["POST"])
def tags_edit(tag_id):
    """Handle form submission for updating an existing tag"""

    tag = Tag.query.get_or_404(tag_id)
    tag.name = request.form['name']
    post_ids = [int(num) for num in request.form.getlist("posts")]
    tag.posts = Post.query.filter(Post.id.in_(post_ids)).all()

    db.session.add(tag)
    db.session.commit()
    flash(f"Tag '{tag.name}' edited.")

    return redirect("/tags")

@app.route('/tags/<int:tag_id>/delete', methods=["POST"])
def tags_delete(tag_id):
    """Handle form submission for deleting a tag"""
    
    tag = Tag.query.get_or_404(tag_id)

    # Remove the tag from posts (assuming you have a many-to-many relationship)
    for post in tag.posts:
        post.tags.remove(tag)

    db.session.delete(tag)
    db.session.commit()
    flash(f"Tag '{tag.name}' deleted.")

    return redirect('/tags')

