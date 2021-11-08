# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    profile = Column(String(2000), nullable=False)
    crated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False)


class Tweet(Base):
    __tablename__ = 'tweets'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False, index=True)
    tweet = Column(String(300), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    user = relationship('User')


class UsersFollowList(Base):
    __tablename__ = 'users_follow_list'

    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    follow_user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    follow_user = relationship('User', primaryjoin='UsersFollowList.follow_user_id == User.id')
    user = relationship('User', primaryjoin='UsersFollowList.user_id == User.id')
