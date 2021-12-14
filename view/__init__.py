import json
from flask import Flask,request,g,Response,current_app,send_file
from werkzeug.utils import secure_filename
from JsonEncoding import CustomJSONEncoder
from functools import wraps
import jwt


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
            
            if user_id is not None:
                g.user_id = user_id
            else:
                return Response(status=403)
        else:
            return Response(status=401)
        
        return f(*arg,**kwargs)
    return decorated_function

#엔드포인트 정의
def create_endpoints(app,service):

    app.json_encoder = CustomJSONEncoder

    user_service = service.user_service
    tweet_service = service.tweet_service


    #api서버의 운행여부를 체크하는 엔드포인드 - health check   
    @app.route("/ping", methods=["GET"])
    def ping():
        return "pong"

    #회원 가입 엔드 포인트
    @app.route("/sign-up",methods=["POST"])
    def sign_up():
        new_user = request.json
        
        created_user = user_service.create_new_user(new_user)

        if created_user is None:
            return "sign up fail",404

        return json.dumps(created_user)
    
    #로그인 엔드포인트 - 성공시에 유저 id 와 엑세스 토큰을 리턴해줌
    @app.route("/login",methods=["POST"])
    def login():
        credential = request.json
        authorized = user_service.login(credential)

        #로그인 실패
        if authorized is False or authorized is None:
            return "login fail",401
        
        else:
            user_credential = user_service.get_user_id_passwd(credential['email'])
            user_id = user_credential["id"]
            token = user_service.generate_access_token(user_id)

            return_result = {
                "user_id": user_id,
                "access_token":token
            }

            return json.dumps(return_result)
    
    # 300자 이내의 트윗 올리기
    # {"id":1,
    # "tweet": "My First tweet"}
    @app.route("/tweet", methods = ["POST"])
    @login_required
    def tweet():
        user_tweet = request.json
        user_tweet['id'] = g.user_id

        #글자수를 반환해서 300자 미만인지 확인하도록 함.
        tweet_result = tweet_service.insert_tweet(user_tweet)
        if tweet_result == "length error":
            return 'tweet length 300 over', 400
        elif tweet_result is None:
            return "tweet add fail",400

        return 'tweet add success',200

    #팔로우 추가하는 엔드포인트
    @app.route("/follow",methods=["POST"])
    @login_required
    def follow():
        payload = request.json
        # user_id = g.user_id
        # follow_id = payload['follow']
        payload["id"] = g.user_id

        #"success"면 성공, "error"면 실패
        if user_service.follow(payload) is None:
            return "follow fail",404

        return 'follow add success',200

    #팔로우 추가하는 엔드포인트
    @app.route("/unfollow",methods=["POST"])
    @login_required
    def unfollow():
        payload = request.json
        payload['id'] = g.user_id

        #"success"면 성공, "error"면 실패
        if user_service.unfollow(payload) is None:
            return "unfollow fail",404

        return 'unfollow success',200

    #타임라인 조회
    @app.route("/timeline",methods=['GET'])
    @login_required
    def timeline():
        user_id = g.user_id

        #None이면 에러
        timeline_result = tweet_service.get_timeline(user_id)

        # if timeline_result == "error":
        #     return Response(status=400)

        return_result = {
            "user_id":1,
            "timeline": timeline_result
        }

        return json.dumps(return_result)

    #프로파일 이미지 저장
    @app.route('/profile-picture',methods=['POST'])
    @login_required
    def upload_profile_picture():
        user_id = g.user_id

        if 'profile_picture' not in request.files:
            return 'File is missing', 404

        profile_picture = request.files['profile_picture']
        print(profile_picture)
        print(f"type: {type(profile_picture)}")

        if profile_picture.filename == '':
            return 'Filename is missing',404

        filename = secure_filename(profile_picture.filename)
        
        temp = user_service.save_profile_picture(profile_picture,filename,user_id)

        return str(temp),200

    #프로파일 이미지 불러오기 - 누구든 볼수 있어야 하므로 인증은 뺸다.
    #불러오고자 하는 유저 id를 url에 넣어서 보낸다.
    @app.route('/profile-picture-get/<int:user_id>', methods=['GET'])
    def get_profile_picture(user_id):
        #이미지 경로를 가져옴
        profile_picture = user_service.get_profile_picture(user_id)

        if profile_picture is not None:
            # return send_file(profile_picture)
            return json.dumps({"img_url":profile_picture})

        else:
            return 'not fount file',404

