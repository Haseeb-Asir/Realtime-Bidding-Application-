# database schema for the bidding app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base
# database connection string for postgreSQL
DATABASE_URL = 'postgresql://postgres:admin123@localhost:5432/bidding_app'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# pydantic models for data validation
from pydantic import BaseModel
