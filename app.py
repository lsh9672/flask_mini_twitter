from flask import Flask,jsonify,request,current_app,Response,g
from flask_cors import CORS
import sqlalchemy
from JsonEncoding import CustomJSONEncoder  
from sqlalchemy import create_engine,or_
from sqlalchemy.orm import session, sessionmaker
from models.model import User,Tweet,UsersFollowList
import json
import bcrypt
import jwt
from datetime import datetime,timedelta
#데코레이션 함수를 만들기 위한 모듈
from functools import wraps

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

#유저 비밀번호 조회 - 이메일로 조회
def get_user_id_passwd(email):
    Session = sessionmaker(bind=current_app.database)
    session = Session()

    #user_id,password
    user_info = session.query(User.id,User.hashed_password).filter(User.email==email).first()
    return_result = dict()
    session.close()
    if user_info:

        return_result = {"id":user_info[0],"hashed_password":user_info[1]}
        return return_result
    else:
        return None


#유저 생성하는 함수(인자 - dict)
def insert_user(new_user):
    
    new_user_id = ""
    Session = sessionmaker(bind=current_app.database)
    session = Session()
    #new user data insert
    new_user['password'] = bcrypt.hashpw(new_user['password'].encode('UTF-8'),bcrypt.gensalt())
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
    except:
        return "error"
    session.close()
    return "success"
    
#팔로우 추가하는 함수
def insert_follow(user_follow):
    Session = sessionmaker(bind = current_app.database)
    session = Session()
    try:
        follow_info = UsersFollowList(user_id=user_follow['id'],follow_user_id = user_follow['follow'])
        session.add(follow_info)
        session.commit()
    except:
        return "error"
    session.close()
    return "success"

#팔로우 추가하는 함수
def insert_unfollow(user_unfollow):
    Session = sessionmaker(bind = current_app.database)
    session = Session()
    try:
        unfollow_info = session.query(UsersFollowList).filter(UsersFollowList.user_id == user_unfollow['id'],UsersFollowList.follow_user_id == user_unfollow['unfollow']).first()
        session.delete(unfollow_info)
        session.commit()
    except:
        return "error"
    session.close()
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

    session.close()

    return timeline

#데코레이터 함수 만들기 - JWT를 복호화해서 인증하는 토큰
def login_required(f):
    @wraps(f)
    def decorated_function(*arg,**kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:   
                #jwt의 decode는 토큰이 유효한지도 검사함
                payload = jwt.decode(access_token,current_app.config['JWT_SECRET_KEY'],'HS256')
            except jwt.InvalidTokenError:
                payload = None
            
            if payload is None:
                return Response(status=401)
            
            user_id = payload['user_id']
            g.user_id = user_id
            
            if user_id is not None:
                g.user = get_user(user_id)
            else:
                g.user=None
        else:
            return Response(status=401)
        
        return f(*arg,**kwargs)
    return decorated_function
            

def create_app(test_config = None):
    app = Flask(__name__)

    CORS(app)

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

    #로그인 엔드포인트
    @app.route("/login",methods=["POST"])
    def login():
        credential = request.json
        email = credential['email']
        password = credential['password']
        user_id_and_password= get_user_id_passwd(email)

        if user_id_and_password is None:
            return "Not Found user",404
        
        else:
            if bcrypt.checkpw(password.encode('UTF-8'),user_id_and_password['hashed_password'].encode('UTF-8')):
                user_id = user_id_and_password['id']
                payload = {
                    "user_id":user_id,
                    "exp":datetime.utcnow()+timedelta(seconds=60*60*24)
                }
                token = jwt.encode(payload,app.config['JWT_SECRET_KEY'],'HS256')
                return json.dumps({
                    "access_token":token
                })
            return 'not invalid token',401


    # 300자 이내의 트윗 올리기
    # {"id":1,
    # "tweet": "My First tweet"}
    
    @app.route("/tweet", methods = ["POST"])
    @login_required
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']
        user_tweet['id'] = g.user_id

        if len(tweet) > 300:
            return 'tweet length 300 over', 400

        insert_result = insert_tweet(user_tweet)
        if insert_result == "error":
            return Response(status=400)

        return 'tweet add success',200

    #팔로우 추가하는 엔드포인트
    @app.route("/follow",methods=["POST"])
    @login_required
    def follow():
        payload = request.json
        payload['id'] = g.user_id

        insert_result = insert_follow(payload)
        if insert_result == "error":
            return Response(status=400)

        return 'follow add success',200

    #팔로우 추가하는 엔드포인트
    @app.route("/unfollow",methods=["POST"])
    @login_required
    def unfollow():
        payload = request.json
        payload['id'] = g.user_id

        delete_result = insert_unfollow(payload)
        if delete_result == "error":
            return Response(status=400)

        return 'unfollow success',200
        
    #타임라인 조회
    @app.route("/timeline",methods=['GET'])
    @login_required
    def timeline():
        user_id = g.user_id
        timeline_result = get_timeline(user_id)
        if timeline_result == "error":
            return Response(status=400)

        return json.dumps(timeline_result)

    @app.route("/timeline2/<int:user_id>",methods=['GET'])
    @login_required
    def timeline2(user_id):
        timeline_result = get_timeline(user_id)
        if timeline_result == "error":
            return Response(status=400)

        result_json = {
            "user_id":user_id,
            "timeline":timeline_result
        }
        return json.dumps(result_json)

    return app







