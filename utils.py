# utils.py
import json
import os

# ---------------- CONFIG ----------------
DATA_FILE = "data.json"
REFERRAL_REWARD = 2.5  # Coins earned per referral

# ---------------- DATA HANDLING ----------------
def load_data():
    """Load data from the JSON file. Returns an empty dict if file is empty or corrupt."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f, indent=4)
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    """Save the given dictionary to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- USER HANDLING ----------------
def ensure_user(user_id, username=None):
    """
    Ensure a user exists in the data with all required fields.
    Returns the user's data dict.
    """
    data = load_data()
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {
            "name": username or f"User{user_id}",
            "referrals": [],
            "salary": 0,
            "coins": 0,
            "activated": False,
            "referred_by": None,
            "joined_channel": False
        }
    else:
        user = data[user_id]
        # Auto-repair missing fields
        user.setdefault("name", username or f"User{user_id}")
        user.setdefault("referrals", [])
        user.setdefault("salary", 0)
        user.setdefault("coins", 0)
        user.setdefault("activated", False)
        user.setdefault("referred_by", None)
        user.setdefault("joined_channel", False)

    save_data(data)
    return data[user_id]

# ---------------- REFERRAL HANDLING ----------------
def add_referral(user_id, referrer_id):
    """
    Add a referral. Increases coins for both the referrer and the new user.
    """
    data = load_data()
    user_id = str(user_id)
    referrer_id = str(referrer_id)

    # Ensure both users exist
    user = ensure_user(user_id)
    referrer = ensure_user(referrer_id)

    if user.get("referred_by") is None and referrer_id != user_id:
        user["referred_by"] = referrer_id
        referrer["coins"] += REFERRAL_REWARD
        user["coins"] += REFERRAL_REWARD
        if user_id not in referrer["referrals"]:
            referrer["referrals"].append(user_id)
        save_data(data)
        return True  # Referral added successfully
    return False  # Referral already exists or invalid
