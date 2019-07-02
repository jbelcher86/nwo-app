#!/usr/bin/env python2.7

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Faction(Base):
    __tablename__ = 'faction'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        '''Return object data in easily serializable format'''
        return {
            'id': self.id,
            'name': self.name,
        }


class Wrestler(Base):
    __tablename__ = 'wrestler'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    finisher = Column(String(50))
    description = Column(String(250))
    faction_id = Column(Integer, ForeignKey('faction.id'))
    faction = relationship(Faction)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        '''Return object data in easily serializeable format'''
        return {
            'faction': self.faction.name,
            'finisher': self.finisher,
            'description': self.description,
            'name': self.name,
            'id': self.id
              }


engine = create_engine('sqlite:///nwo.db')
Base.metadata.create_all(engine)
