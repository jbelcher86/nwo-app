from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Faction, Wrestler

engine = create_engine('sqlite:///nwo.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

Dummy_User = User(name='Johnny Tejas', email = 'theJT@hotmail.biz', picture = 'https://pbs.twimg.com/profile_images/700135459842826240/amPq1IHP_400x400.jpg')

session.add(Dummy_User)
session.commit()

faction1 = Faction(user_id=1, name='nWo Hollywood')
session.add(faction1)
session.commit()

faction2 = Faction(user_id=1, name='nWo Wolfpac')
session.add(faction2)
session.commit()

faction3 = Faction(user_id=1, name='nWo B-Team')
session.add(faction3)
session.commit()

wrestler1 = Wrestler(name='Hulk Hogan', user_id=1, finisher = 'Atomic Leg Drop', description = 'If you needed to name one wrestler, you probably named Hulk Hogan', faction = faction1)
session.add(wrestler1)
session.commit()

wrestler2 = Wrestler(name='Sting', user_id=1, finisher = 'Scorpion Death Lock', description = 'Sting rode throught the nineties proving that good wrestlers borrow, but the best wrestlers steal', faction = faction2)
session.add(wrestler2)
session.commit()

wrestler3 = Wrestler(name='The Giant', user_id=1, finisher = 'Choke Slam', description = 'Well... its the Big Show', faction = faction3)
session.add(wrestler3)
session.commit()

factions = session.query(Faction).all()
for faction in factions:
    print (faction.name)

wrestlers = session.query(Wrestler).all()
for wrestler in wrestlers:
    print (wrestler.description)