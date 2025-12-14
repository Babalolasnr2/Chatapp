from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS # Import CORS

app = Flask(__name__)
# 1. CORS Configuration: Allows connection from the client, regardless of origin/port
# Replace '*' with your specific client URL in production (e.g., 'http://127.0.0.1:8000')
CORS(app, resources={r"/*": {"origins": "*"}}) 
app.config['SECRET_KEY'] = 'your_secret_key' # Important for SocketIO

# Initialize SocketIO, allowing message_queue for production deployment
socketio = SocketIO(app, cors_allowed_origins="*", message_queue=None)

# 2. Basic Route to serve the HTML file (Optional, if frontend is separate)
@app.route('/')
def index():
    # If serving the HTML/JS from the same Flask app, use render_template
    # return render_template('index.html') 
    return "Chat Server Running"

# 3. Handle a new client connection
@socketio.on('connect')
def test_connect():
    print('Client connected!')
    # In a 2-person chat, you might track the two connected users here

# 4. Handle a message event from the client
@socketio.on('send_message')
def handle_message(data):
    # data will contain the message content and sender info
    message_content = data['message']
    sender = data['user']
    print(f"Received message from {sender}: {message_content}")

    # Broadcast the message to all connected clients (the other person)
    # The 'json=True' ensures it's sent as a clean JSON object
    emit('receive_message', {'user': sender, 'message': message_content}, broadcast=True)

# 5. Handle a client disconnection
@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Start the server on port 5000
    socketio.run(app, host='0.0.0.0', port=5000)
    
