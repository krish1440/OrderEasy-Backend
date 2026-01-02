from app.core.security import hash_password

plain_password = "abhay@1999"   # 🔴 change this password

hashed = hash_password(plain_password)

print("Plain Password:", plain_password)
print("Hashed Password:")
print(hashed)
