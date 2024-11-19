from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Store active connections
connections = {}

def get_local_ip():
    try:
        # For Azure, we'll just return the hostname
        return request.host
    except:
        return "Could not get address"

@app.route('/')
def home():
    address = get_local_ip()
    return render_template('index.html', ip_address=address)

@socketio.on('connect')
def handle_connect():
    connections[get_local_ip()] = request.sid

@socketio.on('connect_request')
def handle_connection_request(data):
    target_ip = data['target_ip']
    if target_ip in connections:
        # Create a unique room for these two users
        room = f"{min(request.sid, connections[target_ip])}-{max(request.sid, connections[target_ip])}"
        join_room(room)
        join_room(request.sid)  # Private room for user
        emit('connection_success', {'room': room}, room=request.sid)
        emit('connection_request', {'room': room}, room=connections[target_ip])
    else:
        emit('waiting_for_peer', room=request.sid)

@socketio.on('accept_connection')
def handle_accept_connection(data):
    room = data['room']
    join_room(room)
    emit('chat_started', room=room)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']
    emit('new_message', {'message': message}, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    # Clean up connections
    ip = next((ip for ip, sid in connections.items() if sid == request.sid), None)
    if ip:
        del connections[ip]

if __name__ == '__main__':
    socketio.run(app) 