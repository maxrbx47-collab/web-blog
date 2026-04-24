from unittest import result

from flask import flash, Flask, render_template, redirect, request, url_for
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = '15267434:7fhvs@g45'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

connection = sqlite3.connect('sqlite.db', check_same_thread=False)
cursor = connection.cursor()

class User(UserMixin):
    def __init__(self, id, username, password_hash, email):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def close_db(connection = None):
    if connection is not None:
        connection.close()

@app.teardown_appcontext
def close_connection(exception=None):
    close_db()
@app.route('/')
def index(liked_posts=None):
                cursor.execute('''SELECT
                               post.id,
                               post.title,
                               post.content,
                               post.author_id,
                               users.username,
                               COUNT(like.id) AS likes
                            FROM post
                            JOIN
                            users ON post.author_id = users.id
                            LEFT JOIN
                            like ON post.id = like.post_id
                            GROUP BY 
                            post.id, post.title, post.content, post.author_id, users.username''')
                result = cursor.fetchall()
                posts = []
                for post in reversed(result):
                        posts.append({'id': post[0], 'title': post[1], 'content': post[2], 'author_id': post[3], 'username': post[4], 'likes': post[5]})
                        if current_user.is_authenticated:
                            cursor.execute('SELECT post_id FROM like WHERE user_id = ?', (current_user.id, ))
                            likes_result = cursor.fetchall()
                            liked_posts = []
                            for like in likes_result:
                                liked_posts.append(like[0])
                            posts[-1]['liked_posts'] = liked_posts
                context = {'posts': posts}
                return render_template('blog.html', **context)

@app.route('/add/', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute(
            'INSERT INTO post (title, content, author_id) VALUES (?, ?, ?)',
            (title, content, current_user.id)
        )
        connection.commit()
        return redirect(url_for('index'))
    return render_template('add_post.html')

@app.route('/post/<post_id>')
def post(post_id):
    result = cursor.execute('SELECT post.id, post.title, post.content, users.username FROM post JOIN users ON post.author_id = users.id WHERE post.id =?', (post_id,)).fetchone()
    post_dict = {'id': result[0], 'title': result[1], 'content': result[2], 'username': result[3]}
    return render_template('post.html', post=post_dict)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',(username, generate_password_hash(password, method='pbkdf2:sha256'), email)
            )
            connection.commit()
            print('registred user submit')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            print('user already exists!')
    return render_template('register.html')

@login_manager.user_loader
def load_user(user_id):
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2], user[3])
    return None
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()
        if user and User(user[0], user[1], user[2], user[3]).check_password(password):
            login_user(User(user[0], user[1], user[2], user[3]))
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = cursor.execute('SELECT * FROM post WHERE id = ?', (post_id,)).fetchone()
    if post and post[3] ==  current_user.id:
        cursor.execute('DELETE FROM post WHERE id = ?', (post_id,))
        connection.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


def user_is_liking(user_id, post_id):
    like = cursor.execute('SELECT * FROM like WHERE user_id = ? AND post_id = ?', (user_id, post_id)).fetchone()
    return bool(like)


@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    post = cursor.execute('SELECT * FROM post WHERE id = ?', (post_id,)).fetchone()
    if post:
        if user_is_liking(current_user.id, post_id):
            cursor.execute(
                'DELETE FROM like WHERE user_id = ? AND post_id = ?',
                (current_user.id, post_id))
            connection.commit()
            print('You unliked this post.')
        else:
            cursor.execute(
                'INSERT INTO like (user_id, post_id) VALUES (?, ?)',
                (current_user.id, post_id))
            connection.commit()
            print('You liked this post!')
        return redirect(url_for('index'))
    return 'Post not found', 404





if __name__ == "__main__":
    app.run()
