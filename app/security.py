from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(
        password: str,
        hashed_password: str
) -> bool:
    return (password_hasher.verify(password=password, hash=hashed_password))


if __name__ == '__main__':
    hashed = hash_password("TestPassword123!")

    print(hashed != "TestPassword123!")
    print(verify_password("TestPassword123!", hashed))
    print(verify_password("wrong", hashed))