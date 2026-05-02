# main file for all application logic
from database import schema,model 
from sqlalchemy.orm import Session
from functions import mainfunc
from fastapi import FastAPI, Depends
import uvicorn

app = FastAPI()
@app.post("/users/")
def create_user(user: schema.UserCreate, db: Session = Depends(schema.get_db)):
    return mainfunc.create_user(db, user)

@app.post("/products/")
def create_product(product: schema.ProductCreate, db: Session = Depends(schema.get_db)):
    
    mainfunc.create_product(db, product)
    mainfunc.get_or_create_room(db, product.product_id)
    return {"message": "Product created and room initialized successfully"}


@app.post("/rooms/")
def create_room(product_id: int, db: Session = Depends(schema.get_db)):
    return mainfunc.get_or_create_room(db, product_id)

# shows all running rooms 
@app.get("/rooms/{room_id}/")
def get_rooms(room_id: int, db: Session = Depends(schema.get_db)):
    room = db.query(model.Room).filter(model.Room.room_id == room_id).first()
    if not room:
        raise Exception("Room not found")
    return 
    {
        "room_id": room.room_id,
        "product_id": room.product_id,
        "highest_bid_price": room.highest_bid_price,
        "end_time": room.end_time
    }

@app.post("/bid/")
def place_bid(room_id: int, user_id: int, bid_amount: float, db: Session = Depends(schema.get_db)):
    try:
        mainfunc.bid(db, room_id, user_id, bid_amount)
        return {"message": "Bid placed successfully"}
    except Exception as e:
        return {"error": str(e)}
