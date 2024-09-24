from sqlalchemy.orm import sessionmaker
from models import User, engine
import bcrypt

# Buat sesi
Session = sessionmaker(bind=engine)

# Fungsi untuk menambahkan pengguna
def add_sample_users():
    session = Session()  # Buat sesi baru
    try:
        # Daftar pengguna contoh dengan password yang di-hash
        users = [
            User(username="admin", password=bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())),
            User(username="user1", password=bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt())),
            User(username="user2", password=bcrypt.hashpw("password456".encode('utf-8'), bcrypt.gensalt())),
        ]

        # Menambahkan pengguna ke database
        for user in users:
            existing_user = session.query(User).filter_by(username=user.username).first()
            if existing_user:
                print(f"Pengguna {user.username} sudah ada, tidak ditambahkan.")
            else:
                session.add(user)
                print(f"Menambahkan pengguna: {user.username}")

        session.commit()
        print("Pengguna contoh telah ditambahkan!")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        session.close()  # Pastikan sesi ditutup

if __name__ == "__main__":
    add_sample_users()
