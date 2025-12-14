from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": ["*"],  # For development, restrict in production
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# In-memory storage (use database in production)
messages = []
users = {}  # {user_id: username}
active_users = set()

# Track last message time for each conversation
last_activity = {}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Chat API is running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "register": "/register (POST)",
            "login": "/login (POST)",
            "send_message": "/send (POST)",
            "get_messages": "/messages (GET)",
            "get_users": "/users (GET)",
            "logout": "/logout (POST)"
        }
    })

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    username = data.get('username')
    user_id = data.get('user_id') or f"user_{len(users) + 1}"
    
    if username in [u['username'] for u in users.values()]:
        return jsonify({"error": "Username already exists"}), 400
    
    users[user_id] = {
        'username': username,
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'is_online': False
    }
    
    return jsonify({
        "message": "Registration successful",
        "user": users[user_id]
    }), 201

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    
    if user_id and user_id in users:
        users[user_id]['is_online'] = True
        active_users.add(user_id)
        return jsonify({
            "message": "Login successful",
            "user": users[user_id],
            "active_users": len(active_users)
        })
    elif username:
        # Find user by username
        for uid, user_data in users.items():
            if user_data['username'] == username:
                users[uid]['is_online'] = True
                active_users.add(uid)
                return jsonify({
                    "message": "Login successful",
                    "user": users[uid],
                    "active_users": len(active_users)
                })
    
    return jsonify({"error": "User not found"}), 404

@app.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    if user_id in users:
        users[user_id]['is_online'] = False
        active_users.discard(user_id)
    
    return jsonify({"message": "Logout successful"})

@app.route('/send', methods=['POST', 'OPTIONS'])
def send_message():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    message_text = data.get('message')
    
    if not all([sender_id, receiver_id, message_text]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if sender_id not in users:
        return jsonify({"error": "Sender not found"}), 404
    
    if receiver_id not in users:
        return jsonify({"error": "Receiver not found"}), 404
    
    message = {
        'id': len(messages) + 1,
        'sender_id': sender_id,
        'sender_name': users[sender_id]['username'],
        'receiver_id': receiver_id,
        'receiver_name': users[receiver_id]['username'],
        'message': message_text,
        'timestamp': datetime.now().isoformat(),
        'read': False
    }
    
    messages.append(message)
    
    # Update last activity for this conversation
    conversation_key = tuple(sorted([sender_id, receiver_id]))
    last_activity[conversation_key] = datetime.now().isoformat()
    
    return jsonify({
        "message": "Message sent successfully",
        "data": message
    }), 201

@app.route('/messages', methods=['GET', 'OPTIONS'])
def get_messages():
    if request.method == 'OPTIONS':
        return '', 200
    
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    
    if not user1 or not user2:
        return jsonify({"error": "Both user1 and user2 parameters are required"}), 400
    
    # Filter messages between these two users
    conversation_messages = [
        msg for msg in messages
        if {msg['sender_id'], msg['receiver_id']} == {user1, user2}
    ]
    
    # Mark messages as read
    for msg in conversation_messages:
        if msg['receiver_id'] == user1 and not msg['read']:
            msg['read'] = True
    
    return jsonify({
        "messages": conversation_messages,
        "count": len(conversation_messages),
        "participants": [
            users.get(user1, {}).get('username', 'Unknown'),
            users.get(user2, {}).get('username', 'Unknown')
        ]
    })

@app.route('/users', methods=['GET', 'OPTIONS'])
def get_users():
    if request.method == 'OPTIONS':
        return '', 200
    
    user_list = [
        {
            'user_id': uid,
            'username': data['username'],
            'is_online': uid in active_users,
            'created_at': data['created_at']
        }
        for uid, data in users.items()
    ]
    
    return jsonify({
        "users": user_list,
        "total_users": len(users),
        "active_users": len(active_users)
    })

@app.route('/users/<user_id>', methods=['GET', 'OPTIONS'])
def get_user(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(users[user_id])

@app.route('/check_messages', methods=['GET', 'OPTIONS'])
def check_new_messages():
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = request.args.get('user_id')
    last_check = request.args.get('last_check')
    
    if not user_id:
        return jsonify({"error": "user_id parameter is required"}), 400
    
    # Get unread messages for this user
    unread_messages = [
        msg for msg in messages
        if msg['receiver_id'] == user_id and not msg['read']
    ]
    
    # Get all conversations for this user
    conversations = {}
    for msg in messages:
        if user_id in [msg['sender_id'], msg['receiver_id']]:
            other_user = msg['receiver_id'] if msg['sender_id'] == user_id else msg['sender_id']
            if other_user not in conversations:
                conversations[other_user] = {
                    'user_id': other_user,
                    'username': users.get(other_user, {}).get('username', 'Unknown'),
                    'last_message': msg['message'],
                    'last_time': msg['timestamp'],
                    'unread_count': len([m for m in messages 
                                       if m['receiver_id'] == user_id 
                                       and m['sender_id'] == other_user 
                                       and not m['read']])
                }
    
    return jsonify({
        "unread_messages": unread_messages,
        "unread_count": len(unread_messages),
        "conversations": list(conversations.values())
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
