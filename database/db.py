from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime, date
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_subscribed = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    joined_date = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    total_operations = Column(Integer, default=0)

class UsageStat(Base):
    __tablename__ = 'usage_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id'), index=True)
    operation_type = Column(String(50))
    file_size = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)

class Database:
    def __init__(self):
        try:
            # استخدام NullPool لتجنب مشاكل الاتصال
            self.engine = create_engine(
                DATABASE_URL,
                poolclass=NullPool if 'postgresql' in DATABASE_URL else None,
                echo=False
            )
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_user(self, telegram_id, username=None, first_name=None, last_name=None):
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                self.session.add(user)
                self.session.commit()
                logger.info(f"New user added: {telegram_id}")
            return user
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding user: {e}")
            raise
    
    def update_subscription(self, telegram_id, is_subscribed):
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.is_subscribed = is_subscribed
                user.last_activity = datetime.utcnow()
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating subscription: {e}")
    
    def add_usage_stat(self, user_id, operation_type, file_size=0, success=True):
        try:
            stat = UsageStat(
                user_id=user_id,
                operation_type=operation_type,
                file_size=file_size,
                success=success
            )
            self.session.add(stat)
            
            user = self.session.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.total_operations += 1
                user.last_activity = datetime.utcnow()
            
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding usage stat: {e}")
    
    def get_stats(self):
        try:
            total_users = self.session.query(User).count()
            subscribed_users = self.session.query(User).filter_by(is_subscribed=True).count()
            total_operations = self.session.query(UsageStat).count()
            today = date.today()
            active_today = self.session.query(User).filter(
                User.last_activity >= today
            ).count()
            
            return {
                'total_users': total_users,
                'subscribed_users': subscribed_users,
                'total_operations': total_operations,
                'active_today': active_today
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_users': 0,
                'subscribed_users': 0,
                'total_operations': 0,
                'active_today': 0
            }
    
    def get_all_users(self):
        try:
            return self.session.query(User).order_by(User.joined_date.desc()).all()
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def ban_user(self, telegram_id):
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.is_banned = True
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error banning user: {e}")
            return False
    
    def unban_user(self, telegram_id):
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.is_banned = False
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error unbanning user: {e}")
            return False
    
    def is_banned(self, telegram_id):
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            return user and user.is_banned
        except Exception as e:
            logger.error(f"Error checking ban status: {e}")
            return False
