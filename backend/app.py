from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import redis
import uuid
import threading
import os

app = Flask(__name__, static_folder="../frontend", static_url_path="")
socketio = SocketIO(app, cors_allowed_origins="*")

r = redis.Redis(host='redis', port=6379, decode_responses=True)

orders = {}

# Serve frontend
@app.route('/')
def serve_ui():
    return send_from_directory('../frontend', 'index.html')

@app.route('/order', methods=['POST'])
def create_order():
    data = request.json
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "item": data.get("item"),
        "status": "PLACED"
    }
    r.publish('orders', f"{order_id}:PLACED")
    return jsonify({"order_id": order_id, "status": "PLACED"})

@app.route('/order/<order_id>', methods=['PUT'])
def update_order(order_id):
    status = request.json.get("status")
    if order_id in orders:
        orders[order_id]['status'] = status
        r.publish('orders', f"{order_id}:{status}")
        return jsonify({"msg": "updated"})
    return jsonify({"error": "not found"}), 404

@socketio.on('connect')
def handle_connect():
    print("Client connected")

def redis_listener():
    pubsub = r.pubsub()
    pubsub.subscribe('orders')
    for message in pubsub.listen():
        if message['type'] == 'message':
            socketio.emit('order_update', message['data'])

threading.Thread(target=redis_listener, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

