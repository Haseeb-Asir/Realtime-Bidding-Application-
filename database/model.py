# postgre models for the bidding app
from sqlalchemy import Column, DateTime, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String,unique=True,nullable=True)
    customer_type = Column(String, nullable=False)  # 'buyer' or 'seller'


class Product(Base):
    __tablename__ = 'Products'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    starting_price = Column(Float, nullable=False)
    time_left = Column(Integer, nullable=False)  # time left in seconds
    final_price = Column(Float, nullable=True)

class Room(Base):
    __tablename__ = 'Rooms'
    room_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('Products.product_id'))
    highest_bid_price = Column(Float, nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False) 
    current_highest_bidder_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)

class Bids(Base):
    __tablename__ = 'Bids'
    bid_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('Rooms.room_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    bid_amount = Column(Float, nullable=False)
    bid_time = Column(DateTime(timezone=True), nullable=False)

