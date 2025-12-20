from werkzeug.security import generate_password_hash, check_password_hash
from repositories.user_repository import UserRepository
from models.user import User

class AuthService:
    def __init__(self):
        self.userRepo = UserRepository()

    def register(self, email, password):
        if self.userRepo.getByEmail(email):
            return False
        passwordHash = generate_password_hash(password)
        return self.userRepo.add(User(email, passwordHash))

    def authenticate(self, email, password):
        user = self.userRepo.getByEmail(email)
        if not user:
            return False
        return check_password_hash(user.passwordHash, password)