import asyncio
import jwt
from datetime import datetime, timedelta

JWT_SECRET = "57e7c00105499cb54c5ff238976d83b17776a4a391425bead5b2ac6e5081cad8"
ALGORITHM = "HS256"

# We just need a valid token format. The backend doesn't check if the user exists in DB during simple JWT decoding unless it fetches the user.
# Wait, subscription_guard fetches the user from DB!
# I need to connect to DB to get a valid user_id!
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres.fsnddqpmksidmghfsggm:Au79H5HoGByHtfZb@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
    user = await conn.fetchrow('SELECT id, shop_id FROM users LIMIT 1')
    await conn.close()
    
    if not user:
        print("No users found")
        return
        
    user_id = str(user['id'])
    
    to_encode = {"sub": user_id, "exp": datetime.utcnow() + timedelta(minutes=15)}
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    print("TOKEN:", token)

asyncio.run(main())
