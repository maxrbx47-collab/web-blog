from werkzeug.security import generate_password_hash
import sqlite3
connection = sqlite3.connect('sqlite.db', check_same_thread=False)
cursor = connection.cursor()
result = cursor.execute("CREATE UNIQUE INDEX idx_users_email ON users(email);")
connection.commit()
connection.close()


