

#tweet관련 비즈니스 로직
class TweetService:
    def __init__(self,tweet_dao):
        self.tweet_dao = tweet_dao

    #트윗 길이 확인후에 디비에 넣는 로직
    def insert_tweet(self,user_tweet):
        tweet = user_tweet['tweet']
        if len(tweet) > 300:
            return "length error"
        return self.tweet_dao.insert_tweet(user_tweet)

    #타임 라인 
    def get_timeline(self,user_id):
        return self.tweet_dao.get_timeline(user_id)
