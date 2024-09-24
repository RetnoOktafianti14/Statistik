from sqlalchemy.orm import sessionmaker
from models import User, engine
import bcrypt

# Buat sesi
Session = sessionmaker(bind=engine)

def verify_user(username, password):
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return True
            else:
                print("Password salah untuk user:", username)  # Debugging
        else:
            print("User tidak ditemukan:", username)  # Debugging
    finally:
        session.close()  # Pastikan sesi ditutup

    return False

def add_user(username, password):
    session = Session()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(username=username, password=hashed_password)
        session.add(new_user)
        session.commit()
    finally:
        session.close()  # Pastikan sesi ditutup
