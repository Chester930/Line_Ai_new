import asyncio
from cryptography.hazmat.primitives.asymmetric import rsa

async def rotate_jwt_keys():
    """自動化金鑰輪替"""
    new_priv_key = generate_private_key()
    new_pub_key = new_priv_key.public_key()
    
    # 漸進式輪替
    await cache.set('jwt:current', new_priv_key)
    await cache.set('jwt:previous', current_priv_key)
    
    # 舊金鑰保留時間
    asyncio.get_event_loop().call_later(
        3600, cache.delete, 'jwt:previous'
    ) 