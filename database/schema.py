# database schema for the bidding app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base

DATABASE_URL = 'postgresql://username:admin123@localhost:5432/bidding_app'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
