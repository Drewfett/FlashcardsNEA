import socketio

sio = socketio.Client()


@sio.event
def message(data):
    pass


@sio.on('*')
def catch_all(event, data):
    pass


@sio.event
def connect():
    print("Client connected!")
    print('my sid is', sio.sid)


@sio.event
def connect_error(data):
    print("The connection failed!")


@sio.event
def disconnect():
    print("Client Disconnected!")


sio.connect('http://localhost:5000')
