from flask import Flask,jsonify,request,current_app
from JsonEncoding import CustomJSONEncoder  
from sqlalchemy import create_engine
from sqlalchemy.orm import session, sessionmaker
from models.model import User,Tweet,UsersFollowList


def create_app(test_config = None):
    app = Flask(__name__)

    app.json_encoder = CustomJSONEncoder

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'],encoding = 'utf-8',max_overflow = 0)
    app.database = database

    #api서버의 운행여부를 체크하는 엔드포인드 - health check   
    @app.route("/ping", methods=["GET"])
    def ping():
        return "pong"

    @app.route("/sign-up",methods=["POST"])
    def sign_up():
        new_user = request.json

        Session = sessionmaker(bind=app.database)
        new_user_id = ""

        #new user data insert
        session = Session()
        
        user_info = User(name=new_user['name'],email=new_user['email'],profile=new_user['profile'],hashed_password=new_user['password'])
        session.add(user_info)
        session.commit()
        new_user_id = user_info.id
        print(new_user_id)

        #new user data select
        row = session.query(User.id,User.name,User.email,User.profile).filter(User.id==new_user_id).first()
        print("check",row)

        if row is not None:
            created_user={
                'id':row[0],
                'name':row[1],
                'email':row[2],
                'profile':row[3]
            }
        else:
            created_user=None
        
        session.close()

        return jsonify(created_user)

    # 300자 이내의 트윗 올리기
    # {"id":1,
    # "tweet": "My First tweet"}

    @app.route("/tweet", methods = ["POST"])
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']

        if len(tweet) > 300:
            return 'tweet length 300 over', 400

        Session = sessionmaker(bind = app.database)
        session = Session()
        
        tweet_content = Tweet(user_id=int(user_tweet['id']),tweet=user_tweet['tweet'])
        session.add(tweet_content)
        session.commit()
        
        session.close()

        return 'tweet add success',200

    return app






# #팔로우 기능
# @app.route("/follow", mehtods=["POST"])
# def follow():

#     payload = request.json
#     user_id = int(payload['id'])
#     user_id_to_follow = int(payload['follow'])

#     if user_id not in app.users or user_id_to_follow not in app.users:
#         return 'not found user',400
    
#     user = app.users[user_id]
#     user.setdefault('follow',set()).add(user_id_to_follow)

#     return jsonify(user)

# #언팔로우 기능
# @app.route("/unfollow", methods = ["POST"])
# def unfollow():
#     payload = request.json
#     user_id = int(payload["id"])
#     user_id_to_unfollow = int(payload["unfollow"])

#     if user_id not in app.users or user_id_to_unfollow not in app.users:
#         return 'not found user', 400

#     user = app.users[user_id]
#     user.setdefault('follow',set()).discard(user_id_to_unfollow)

#     return jsonify(user)

# #타임라인 기능

# @app.route('/timeline/<int:user_id>',methods=["GET"])
# def timeline(user_id):
#     if user_id not in app.users:
#         return 'not found user', 400

#     follow_list = app.users[user_id].get('follow',set())
#     follow_list.add(user_id)
#     timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

#     return jsonify({'user_id':user_id,'timeline':timeline})
