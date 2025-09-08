import json
import os

DATA_FILE = "data.json"
REFERRAL_REWARD = 2.5

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f, indent=4)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(user_id, username=None):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "name": username or "UNKNOWN",
            "referrals": [],
            "coins": 0,
            "activated": False,
            "referred_by": None,
            "joined_channel": False
        }
    else:
        user = data[user_id]
        user.setdefault("name", username or "UNKNOWN")
        user.setdefault("referrals", [])
        user.setdefault("coins", 0)
        user.setdefault("activated", False)
        user.setdefault("referred_by", None)
        user.setdefault("joined_channel", False)
    save_data(data)
    return data[user_id]
