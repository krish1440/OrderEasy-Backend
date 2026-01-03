from app.core.security import hash_password

plain_password = "krish@8252"   # 🔴 change this password

hashed = hash_password(plain_password)

print("Plain Password:", plain_password)
print("Hashed Password:")
print(hashed)
