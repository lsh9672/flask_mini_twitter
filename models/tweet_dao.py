from sqlalchemy.orm import session, sessionmaker
from .model import User,Tweet,UsersFollowList
from sqlalchemy import or_


#트윗 관련 디비
class TweetDao:
    def __init__(self,database):
        self.db = database

    def insert_tweet(self,user_tweet):
        Session = sessionmaker(bind=self.db)
        session = Session()
        try:
            tweet = Tweet(user_id = user_tweet['id'], tweet = user_tweet['tweet'])
            session.add(tweet)
            session.commit()
        except:
            session.close()
            return None

        session.close()
        return "success"

    def get_timeline(self,user_id):
        Session = sessionmaker(bind=self.db)
        session = Session()
        try:
            rows = session.query(Tweet.user_id,Tweet.tweet).outerjoin(UsersFollowList,UsersFollowList.user_id==user_id).filter(or_(Tweet.user_id==user_id,Tweet.user_id==UsersFollowList.follow_user_id)).all()
            
            timeline=list()
            for row in rows:
                timeline.append({'user_id':row[0],'tweet':row[1]})
        except:
            session.close()
            return None

        session.close()
        return timeline