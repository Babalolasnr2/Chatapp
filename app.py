from flask import Flask, render_template  # <-- ADDED render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS 

app = Flask(__name__)
# Allow connections from any origin (Crucial for testing/CORS)
CORS(app, resources={r"/*": {"origins": "*"}}) 
app.config['SECRET_KEY'] = 'your_secret_key' 

# Initialize SocketIO with cors_allowed_origins="*" for Render compatibility
socketio = SocketIO(app, cors_allowed_origins="*")

# 1. UPDATED ROUTE: Serve the index.html file from the 'templates' folder
@app.route('/')
def index():
    return render_template('index.html') 

# 2. SocketIO EVENT HANDLERS (Unchanged from before)

@socketio.on('connect')
def test_connect():
    print('Client connected!')

@socketio.on('send_message')
def handle_message(data):
    message_content = data['message']
    sender = data['user']
    print(f"Received message from {sender}: {message_content}")

    # Broadcast the message to all connected clients (the other person)
    emit('receive_message', {'user': sender, 'message': message_content}, broadcast=True)

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Use socketio.run instead of app.run for local development
    # In production, this will be run by Gunicorn/Eventlet
    socketio.run(app, host='0.0.0.0', port=5000)
    emit('receive_message', {'user': sender, 'message': message_content}, broadcast=True)

# 5. Handle a client disconnection
@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Start the server on port 5000
    socketio.run(app, host='0.0.0.0', port=5000)
    
