from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import schema, model 
from functions import mainfunc
# Assuming your bid_handler and manager are in a file named bidding_logic.py
import uvicorn

app = FastAPI()

# --- Your existing routes ---

@app.post("/users/")
def create_user(user: schema.UserCreate, db: Session = Depends(schema.get_db)):
    return mainfunc.create_user(db, user)

@app.post("/products/")
def create_product(product: schema.ProductCreate, db: Session = Depends(schema.get_db)):
    # Create product and get the object to access product_id
    new_product = mainfunc.create_product(db, product)
    # Initialize the room for this specific product
    mainfunc.get_or_create_room(db, new_product.product_id)
    return {"message": "Product created and room initialized successfully"}

# --- The WebSocket Route ---
@app.get("/rooms/")
def get_active_rooms(db: Session = Depends(schema.get_db)):
    # 1. Fetch all rooms from the database
    rooms = db.query(model.Room).all()
    
    catalogue = []
    for room in rooms:
        # 2. For each room, fetch the matching product to get its name
        product = db.query(model.Product).filter(model.Product.product_id == room.product_id).first()
        
        if product:
            catalogue.append({
                "room_id": room.room_id,
                "name": product.name,
                "current_price": room.highest_bid_price,
                # Convert datetime to a string so it can be sent as JSON
                "end_time": room.end_time.isoformat() if room.end_time else None 
            })
            
    return catalogue

@app.websocket("/ws/auction/{room_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    user_id: int, 
    db: Session = Depends(schema.get_db)
):
    # This calls the complex logic we wrote earlier (with the locking and broadcasting)
    await mainfunc.bid_handler(websocket, room_id, user_id, db)

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your local HTML file to talk to the server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)