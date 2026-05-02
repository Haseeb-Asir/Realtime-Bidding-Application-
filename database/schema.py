# database schema for the bidding app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.model import Base
# database connection string for postgreSQL
DATABASE_URL = 'postgresql://postgres:admin123@localhost:5432/bidding_app'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# pydantic models for data validation incoming and outgoing data on web/api
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    customer_type: str  # 'buyer' or 'seller'

class ProductCreate(BaseModel):
    name : str
    description : str
    starting_price : float
    time_left : int

class RoomCreate(BaseModel): # activate as soon as someone clicks on the product to bid
    product_id : int
    highest_bid_price : float

class BidsCreate(BaseModel):
    room_id : int
    user_id : int
    bid_amount : float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
