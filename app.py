from flask import Flask,jsonify,request,current_app,Response
import sqlalchemy
from JsonEncoding import CustomJSONEncoder  
from sqlalchemy import create_engine,or_
from sqlalchemy.orm import session, sessionmaker
from models.model import User,Tweet,UsersFollowList
import json

#유저 정보 가져오기
def get_user(user_id):
    Session = sessionmaker(bind=current_app.database)
    session = Session()

    user_info = session.query(User.id,User.name,User.email,User.profile).filter(User.id==user_id).first()
    
    session.close()
    if user_info:
        return {
            "id":user_info[0],
            "name":user_info[1],
            "email":user_info[2],
            "profile":user_info[3]
        }
    else:
        return None

#유저 생성하는 함수(인자 - dict)
def insert_user(new_user):
    
    new_user_id = ""
    Session = sessionmaker(bind=current_app.database)
    session = Session()
    #new user data insert
    
    user_info = User(name=new_user['name'],email=new_user['email'],profile=new_user['profile'],hashed_password=new_user['password'])
    session.add(user_info)
    session.commit()

    new_user_id = user_info.id

    #new user data select
    session.close()
    if new_user_id:
        return new_user_id
    else:
        return None

#트윗을 입력받아서 디비에 넣는 함수
def insert_tweet(user_tweet):
    Session = sessionmaker(bind=current_app.database)
    session = Session()
    try:
        tweet = Tweet(user_id = user_tweet['id'], tweet = user_tweet['tweet'])
        session.add(tweet)
        session.commit()
        session.close()
    except:
        return "error"
    return "success"
    
#팔로우 추가하는 함수
def insert_follow(user_follow):
    Session = sessionmaker(bind = current_app.database)
    session = Session()
    try:
        follow_info = UsersFollowList(user_id=user_follow['id'],follow_user_id = user_follow['follow'])
        session.add(follow_info)
        session.commit()
        session.close()
    except:
        return "error"
    return "success"

#팔로우 추가하는 함수
def insert_unfollow(user_unfollow):
    Session = sessionmaker(bind = current_app.database)
    session = Session()
    try:
        unfollow_info = session.query(UsersFollowList).filter(UsersFollowList.user_id == user_unfollow['id'],UsersFollowList.follow_user_id == user_unfollow['unfollow']).first()
        session.delete(unfollow_info)
        session.commit()
        session.close()
    except:
        return "error"
    return "success"

#타임라인 가져오는 함수
def get_timeline(user_id):
    Session = sessionmaker(bind=current_app.database)
    session = Session()
    try:
        rows = session.query(Tweet.user_id,Tweet.tweet).outerjoin(UsersFollowList,UsersFollowList.user_id==user_id).filter(or_(Tweet.user_id==user_id,Tweet.user_id==UsersFollowList.follow_user_id)).all()
        
        timeline=list()
        for row in rows:
            timeline.append({'user_id':row[0],'tweet':row[1]})
    except:
        return "error"

    return timeline

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

        insert_result_id = insert_user(new_user)
        created_user = get_user(insert_result_id)

        return json.dumps(created_user)

    # 300자 이내의 트윗 올리기
    # {"id":1,
    # "tweet": "My First tweet"}

    @app.route("/tweet", methods = ["POST"])
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']

        if len(tweet) > 300:
            return 'tweet length 300 over', 400

        insert_result = insert_tweet(user_tweet)
        if insert_result == "error":
            return Response(status=400)

        return 'tweet add success',200

    #팔로우 추가하는 엔드포인트
    @app.route("/follow",methods=["POST"])
    def follow():
        payload = request.json

        insert_result = insert_follow(payload)
        if insert_result == "error":
            return Response(status=400)

        return 'follow add success',200

    #팔로우 추가하는 엔드포인트
    @app.route("/unfollow",methods=["POST"])
    def unfollow():
        payload = request.json

        delete_result = insert_unfollow(payload)
        if delete_result == "error":
            return Response(status=400)

        return 'unfollow success',200
    
    #타임라인 조회
    @app.route("/timeline/<int:user_id>",methods=['GET'])
    def timeline(user_id):

        timeline_result = get_timeline(user_id)
        if timeline_result == "error":
            return Response(status=400)

        return json.dumps(timeline_result)

    return app







