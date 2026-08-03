import time

from umqtt.simple import MQTTClient

from config import (
    MQTT__BROKER_ADDRESS,
    MQTT__BROKER_PORT,
    MQTT__KEEPALIVE_SECONDS,
    MQTT__MY_CLIENT_ID,
    MQTT__MY_LAST_WILL_MESSAGE,
    MQTT__MY_LAST_WILL_TOPIC,
    MQTT__MY_PASSWORD,
    MQTT__MY_USERNAME,
)

# TODO: LLM added a lot of try/except blocks
# TODO: the code seems a bit convoluted, maybe I should go over it and simplify it sometime

PING_INTERVAL_MS: int = MQTT__KEEPALIVE_SECONDS * 1000 // 2
RECONNECT_INITIAL_DELAY_MS: int = 1000
RECONNECT_MAX_DELAY_MS: int = 30000
CONNECT_TIMEOUT_SECONDS: int = 5 # without it connect() blocks the whole main loop indefinitely

_client: MQTTClient = None
_is_initialized: bool = False
_is_connected: bool = False
_last_ping_timestamp: int = 0
_next_reconnect_timestamp: int = 0
_reconnect_delay_ms: int = RECONNECT_INITIAL_DELAY_MS

_message_handlers: dict = {}
_subscribed_topics: dict = {} # topic -> qos | stored in case of a disconnect, so they can be restored


def client() -> MQTTClient:
    return _client


def is_initialized() -> bool:
    return _is_initialized


def is_connected() -> bool:
    return _is_connected


def handle_incoming_messages(topic: bytes, message: bytes):
    topic_str: str = topic.decode('utf-8')

    if topic in _message_handlers:
        print(f"[MQTT] received at '{topic_str}', sending to a corresponding handler.")
        try:
            _message_handlers[topic](topic_str, message)
        except Exception as e:
            print(f"[MQTT] handler for '{topic_str}' failed: '{e}'.")
    else:
        print(f"[MQTT] received unhandled topic: '{topic_str}' -> '{message[:50]}'.")


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
        password=MQTT__MY_PASSWORD.encode('utf-8'),
        keepalive=MQTT__KEEPALIVE_SECONDS
    )
    _client.set_last_will(
        topic=MQTT__MY_LAST_WILL_TOPIC.encode('utf-8'),
        msg=MQTT__MY_LAST_WILL_MESSAGE.encode('utf-8'),
        retain=False,
        qos=0
    )
    _client.set_callback(handle_incoming_messages)
    _is_initialized = True


def _schedule_reconnect():
    global _next_reconnect_timestamp, _reconnect_delay_ms
    _next_reconnect_timestamp = time.ticks_add(time.ticks_ms(), _reconnect_delay_ms)
    _reconnect_delay_ms = min(_reconnect_delay_ms * 2, RECONNECT_MAX_DELAY_MS)


def _close_socket(): # free a socket, there are only 16? available on the ESP32
    if _client is None or _client.sock is None:
        return
    try:
        _client.sock.close()
    except Exception:
        pass
    _client.sock = None


def _on_connection_lost(error: Exception):
    global _is_connected, _reconnect_delay_ms
    if not _is_connected:
        return
    _is_connected = False
    _reconnect_delay_ms = RECONNECT_INITIAL_DELAY_MS
    print(f"[MQTT] connection lost: '{error}'.")
    _close_socket()
    _schedule_reconnect()


def _restore_subscriptions() -> bool:
    for topic, qos in _subscribed_topics.items():
        try:
            _client.subscribe(topic.encode('utf-8'), qos)
        except OSError as e:
            _on_connection_lost(e)
            return False
    return True


def connect() -> bool:
    global _is_connected, _last_ping_timestamp, _reconnect_delay_ms
    try:
        _client.connect(timeout=CONNECT_TIMEOUT_SECONDS)
    except Exception as e:
        print(f"[MQTT] failed to connect: '{e}'.")
        _close_socket()
        _schedule_reconnect()
        return False

    _is_connected = True
    _last_ping_timestamp = time.ticks_ms()
    _reconnect_delay_ms = RECONNECT_INITIAL_DELAY_MS
    print("[MQTT] connected.")
    return _restore_subscriptions()


def check_connection_reconnect_if_needed():
    if _is_connected or not _is_initialized:
        return
    if time.ticks_diff(time.ticks_ms(), _next_reconnect_timestamp) < 0:
        return
    print("[MQTT] reconnecting...")
    connect()


def send_message(topic: str, msg: str, retain: bool = False, qos: int = 0) -> bool:
    return send_bytes(topic, msg.encode('utf-8'), retain, qos)


def send_bytes(topic: str, payload: bytes, retain: bool = False, qos: int = 0) -> bool:
    if not _is_connected:
        return False
    try:
        _client.publish(
            topic=topic.encode('utf-8'),
            msg=payload,
            retain=retain,
            qos=qos
        )
    except OSError as e:
        _on_connection_lost(e)
        return False
    return True


def subscribe(topic: str, qos: int = 0) -> bool:
    _subscribed_topics[topic] = qos
    if not _is_connected:
        return False
    try:
        _client.subscribe(topic.encode('utf-8'), qos)
    except OSError as e:
        _on_connection_lost(e)
        return False
    return True


def unsubscribe(topic: str) -> bool:
    _subscribed_topics.pop(topic, None)
    if not _is_connected:
        return False
    try:
        _client.unsubscribe(topic.encode('utf-8'))
    except OSError as e:
        _on_connection_lost(e)
        return False
    return True


def wait_for_any_message__B():
    if not _is_connected:
        return
    try:
        _client.wait_msg()
    except OSError as e:
        _on_connection_lost(e)


def check_if_any_message():
    if not _is_connected:
        return
    try:
        _client.check_msg()
    except OSError as e:
        _on_connection_lost(e)


def ping_if_needed():
    global _last_ping_timestamp
    if not _is_connected or MQTT__KEEPALIVE_SECONDS <= 0:
        return
    if time.ticks_diff(time.ticks_ms(), _last_ping_timestamp) < PING_INTERVAL_MS:
        return
    _last_ping_timestamp = time.ticks_ms()
    try:
        _client.ping()
    except OSError as e:
        _on_connection_lost(e)
