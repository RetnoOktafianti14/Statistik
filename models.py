# models.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

# Ganti URL database sesuai kebutuhan Anda
DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

# Buat tabel jika belum ada
Base.metadata.create_all(engine)
