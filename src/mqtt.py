from umqtt.simple import MQTTClient

from config import *

_client: MQTTClient = None
_is_initialized: bool = False
_is_connected: bool = False

_message_handlers: dict = {}


def client() -> MQTTClient:
    return _client
    
    
def is_initialized() -> bool:
    return _is_initialized
    
    
def is_connected() -> bool:
    return _is_connected
    

def handle_incoming_messages(topic: bytes, message: bytes):
    topic_str: str = topic.decode('utf-8')
    msg_str: str = message.decode('utf-8')

    if topic in _message_handlers:
        print(f"[MQTT] received: '{topic_str}' -> '{msg_str[:50]}', sending to a corresponding handler.")
        _message_handlers[topic](topic_str, msg_str)
    else:
        print(f"[MQTT] received unhandled topic: '{topic_str}' -> '{msg_str[:50]}'.")


def register_handler(topic: str, function):
    _message_handlers.setdefault(topic.encode('utf-8'), function)
    print(f"[MQTT] registered handler for topic: '{topic}'.")


def initialize():
    global _client, _is_initialized
    _client = MQTTClient(
		client_id=MQTT__MY_CLIENT_ID.encode('utf-8'),
		server=MQTT__BROKER_ADDRESS,
		port=MQTT__BROKER_PORT,
        user=MQTT__MY_USERNAME.encode('utf-8'),
        password=MQTT__MY_PASSWORD.encode('utf-8')
    )
    _client.set_last_will(
        topic=MQTT__MY_LAST_WILL_TOPIC.encode('utf-8'),
        msg=MQTT__MY_LAST_WILL_MESSAGE.encode('utf-8'),
        retain=False,
        qos=0
    )
    _client.set_callback(handle_incoming_messages)
    _is_initialized = True
    

def connect():
    global _client, _is_connected
    _client.connect()
    _is_connected = True


def send_message(topic: str, msg: str, retain: bool = False, qos: int = 0):
    global _client
    _client.publish(
        topic=topic.encode('utf-8'),
        msg=msg.encode('utf-8'),
        retain=retain,
        qos=qos
    )
    
    
def subscribe(topic: str, qos: int = 0):
    global _client
    _client.subscribe(topic.encode('utf-8'), qos)
    
    
def unsubscribe(topic: str):
    global _client
    _client.unsubscribe(topic.encode('utf-8'))
    
    
def wait_for_any_message():
    global _client
    _client.wait_msg()
    

def check_if_any_message():
    global _client
    _client.check_msg()
