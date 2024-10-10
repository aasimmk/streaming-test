from collections import defaultdict


users_db = {}
user_id_counter = 1

threads_db = {}
conversations_db = {}
messages_db = {}

active_websocket_connections = defaultdict(list)
