import json
from config import DATA_FILE

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(user_id, username):
    """Ensure the user exists with all required fields."""
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "name": username,
            "salary": 0,
            "coins": 0,
            "joined_channel": False,
            "referred_by": None,
            "referrer_counted": []
        }
        save_data(data)
    else:
        # Make sure old users get missing keys
        user = data[user_id]
        if "salary" not in user:
            user["salary"] = 0
        if "coins" not in user:
            user["coins"] = 0
        if "joined_channel" not in user:
            user["joined_channel"] = False
        if "referred_by" not in user:
            user["referred_by"] = None
        if "referrer_counted" not in user:
            user["referrer_counted"] = []
        save_data(data)
    return data[user_id]
