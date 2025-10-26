from typing import Dict

users_db: Dict[int, dict] = {}


def save_user_data(user_id: int, data: dict):
    users_db[user_id] = data


def get_user_data(user_id: int):
    return users_db.get(user_id)
