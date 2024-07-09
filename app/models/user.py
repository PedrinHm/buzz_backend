from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..config.database import Base
from datetime import datetime
import bcrypt

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    email = Column(String, unique=True)
    cpf = Column(String, unique=True)
    phone = Column(String, unique=True)
    user_type_id = Column(Integer, ForeignKey('user_types.id'))
    system_deleted = Column(String, default="0")
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)
    first_login = Column(String, default="true")

    def verify_password(self, password):
        if not password or not self.password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
