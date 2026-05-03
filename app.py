import streamlit as st
import requests
import json
import websocket  # from websocket-client
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Live Auction House", page_icon="🔨", layout="centered")
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/auction"

# --- SESSION STATE ---
# Streamlit forgets everything when it refreshes. We use session_state to remember who is logged in.
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "current_room" not in st.session_state:
    st.session_state.current_room = None

# --- SIDEBAR: AUTHENTICATION ---
with st.sidebar:
    st.title("🔐 Authentication")
    
    if st.session_state.user_id is None:
        auth_mode = st.radio("Choose Action", ["Login / Register"])
        username = st.text_input("Username")
        email = st.text_input("Email")
        user_type = st.selectbox("I am a...", ["buyer", "seller"])
        
        if st.button("Enter Application"):
            if username and email:
                # HTTP POST to FastAPI to create/login user
                res = requests.post(f"{API_URL}/users/", json={
                    "username": username,
                    "email": email,
                    "customer_type": user_type
                })
                if res.status_code == 200:
                    user_data = res.json()
                    st.session_state.user_id = user_data["user_id"] # Adjust based on your actual DB schema
                    st.session_state.username = username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Failed to connect to backend.")
    else:
        st.success(f"Welcome back, {st.session_state.username}!")
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.current_room = None
            st.rerun()

# --- MAIN APP ROUTING ---
if st.session_state.user_id is None:
    st.info("👈 Please login or register using the sidebar to enter the Auction House.")
    st.stop()

# We use tabs to separate the Seller and Buyer views cleanly
tab1, tab2 = st.tabs(["🛒 Buyer Catalogue", "📦 Seller Dashboard"])

with tab2:
    st.header("Create a New Auction")
    with st.form("create_auction_form"):
        prod_name = st.text_input("Product Name")
        prod_desc = st.text_area("Description")
        start_price = st.number_input("Starting Price ($)", min_value=1.0, value=10.0)
        time_limit = st.number_input("Time Limit (Minutes)", min_value=1, value=5)
        
        submit_product = st.form_submit_button("Launch Auction")
        
        if submit_product:
            res = requests.post(f"{API_URL}/products/", json={
                "name": prod_name,
                "description": prod_desc,
                "starting_price": start_price,
                "time_left": time_limit
            })
            if res.status_code == 200:
                st.success(f"Auction for {prod_name} is now live!")
            else:
                st.error("Failed to create product.")

with tab1:
    if st.session_state.current_room is None:
        st.header("Live Auctions")
        if st.button("🔄 Refresh Catalogue"):
            st.rerun()
            
        # HTTP GET to fetch active rooms (Requires the /rooms route we discussed previously)
        try:
            res = requests.get(f"{API_URL}/rooms/")
            if res.status_code == 200:
                rooms = res.json()
                if not rooms:
                    st.write("No active auctions right now. Check back later!")
                else:
                    for room in rooms:
                        with st.container(border=True):
                            st.subheader(room["name"])
                            st.write(f"**Current Highest Bid:** ${room['current_price']}")
                            # Add a button to join this specific room
                            if st.button("Join Room", key=f"join_{room['room_id']}"):
                                st.session_state.current_room = room
                                st.rerun()
        except Exception as e:
            st.error(f"Make sure your FastAPI server is running! Error: {e}")

    else:
        # --- THE LIVE ROOM VIEW ---
        room = st.session_state.current_room
        st.header(f"Live Room: {room['name']}")
        st.button("⬅️ Back to Catalogue", on_click=lambda: st.session_state.pop("current_room") and None)
        
        # Display current state
        st.metric(label="Current Highest Bid", value=f"${room['current_price']}")
        
        st.markdown("---")
        st.subheader("Place a Bid")
        
        new_bid = st.number_input("Your Bid Amount ($)", min_value=float(room['current_price'] + 1), step=1.0)
        
        if st.button("Submit Bid 🚀"):
            try:
                # 1. Open a temporary, synchronous WebSocket connection
                ws_target = f"{WS_URL}/{room['room_id']}/{st.session_state.user_id}"
                ws = websocket.create_connection(ws_target)
                
                # 2. Send the JSON payload exactly as your FastAPI backend expects it
                payload = json.dumps({"amount": new_bid})
                ws.send(payload)
                
                # 3. Wait for the server's immediate broadcast/response
                response = ws.recv()
                server_msg = json.loads(response)
                
                # 4. Handle the server's logic (Success vs Rejection)
                if server_msg.get("event") == "new_highest_bid":
                    st.success(f"Bid of ${server_msg['amount']} accepted!")
                    # Update local state so the UI reflects the new price
                    st.session_state.current_room['current_price'] = server_msg['amount']
                    ws.close()
                    st.rerun() # Refresh the page to update the metric
                elif "error" in server_msg or server_msg.get("event") == "bid_rejected":
                    st.error(f"Bid rejected: {server_msg.get('msg', 'Unknown error')}")
                    ws.close()
                elif server_msg.get("event") == "auction_ended":
                    st.warning(server_msg.get('msg'))
                    ws.close()
                    
            except Exception as e:
                st.error(f"WebSocket Connection Failed: {e}. Is the server running?")