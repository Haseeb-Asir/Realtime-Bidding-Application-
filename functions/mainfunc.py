# all important functions for the app are defined here
from datetime import datetime, timedelta, timezone

from fastapi import WebSocket, WebSocketDisconnect
from streamlit import json
from database.model import User, Product, Room,Bids
from database.schema import UserCreate, ProductCreate, RoomCreate
from sqlalchemy.orm import Session

def create_user(db: Session , user: UserCreate):
    db_user = User(username=user.username, email=user.email, customer_type=user.customer_type)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_product(db: Session , product: ProductCreate):
    db_product = Product(name=product.name, description=product.description, starting_price=product.starting_price, time_left=product.time_left)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_or_create_room(db: Session, product_id: int):
    # Check if room exists
    db_room = db.query(Room).filter(Room.product_id == product_id).first()
    
    if not db_room:
        # 2. Fetch the product to see what time limit the user set
        product = db.query(Product).filter(Product.product_id == product_id).first()
        
        # 3. Calculate end_time based on user input (product.time_left)
        # Assuming product.time_left is in minutes
        auction_end = datetime.now(timezone.utc)+ timedelta(minutes=product.time_left)
        
        db_room = Room(
            product_id=product_id, 
            highest_bid_price=product.starting_price, 
            end_time =auction_end
        )
        
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        
    return "Room created or already exists with room_id: {}".format(db_room.room_id)



class ConnectionManager:
    def __init__(self):
        # Store connections by room_id: {room_id: [websocket1, websocket2]}
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: int):
        # Send message only to people in this specific room
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()


async def bid_handler(websocket: WebSocket, room_id: int, user_id: int, db: Session):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            new_bid_amount = float(message.get("amount"))

            # Start a transaction for the lock
            try:
                # SELECT ... FOR UPDATE
                # This locks the row. Other requests for this room_id will wait here.
                room = db.query(Room).filter(Room.room_id == room_id).with_for_update().first()

                if not room:
                    await websocket.send_text(json.dumps({"error": "Room not found"}))
                    continue

                # Now that we have the lock, check the price safely
                if new_bid_amount > room.highest_bid_price:
                    # Update Room
                    room.highest_bid_price = new_bid_amount
                    
                    # Create Bid Log
                    new_bid_log = Bid(
                        room_id=room_id,
                        user_id=user_id,
                        bid_amount=new_bid_amount,
                        bid_time=datetime.utcnow()
                    )
                    
                    db.add(new_bid_log)
                    db.commit() # Lock is released ONLY after commit()

                    # Broadcast to everyone
                    await manager.broadcast({
                        "event": "new_highest_bid",
                        "amount": new_bid_amount,
                        "user_id": user_id
                    }, room_id)
                else:
                    db.rollback() # Release lock if bid is too low
                    await websocket.send_text(json.dumps({
                        "event": "bid_rejected",
                        "msg": "Bid too low!"
                    }))

            except Exception as e:
                db.rollback() # Always rollback on error to release the lock
                print(f"Database error: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
