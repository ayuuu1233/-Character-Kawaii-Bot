from shivu.modules.database.db import db # db.py se database instance import karein

# Sudo users collection
sudo_collection = db['sudos']

# 1. Sudo user add 
async def add_to_sudo_users(user_id, username, sudo_title):
    await sudo_collection.update_one(
        {'id': user_id},
        {'$set': {'username': username, 'sudo_title': sudo_title}},
        upsert=True
    )

# 2. Sudo user remove 
async def remove_from_sudo_users(user_id):
    await sudo_collection.delete_one({"id": user_id})

# 3. Check if user is a sudo user 
async def is_user_sudo(user_id):
    user = await sudo_collection.find_one({"id": user_id})
    return bool(user)

# 4 All sudo users list 
async def fetch_sudo_users():
    sudo_list = []
    # Cursor ka use karke database se data fetch karein
    async for user in sudo_collection.find({}):
        sudo_list.append({
            "user_id": user.get('id'),
            "username": user.get('username'),
            "sudo_title": user.get('sudo_title')
        })
    return sudo_list
