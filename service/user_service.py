import bcrypt
from datetime import datetime, timedelta
import jwt
import os


#비즈니스 로직 - 실질적으로 유저를 추가하고 트윗을 추가하는 등의 로직이 들어감
#UserService에는 사용자생성, 팔로우, 언팔로우 등의 사용자 관련된 로직이 들어감.
class UserService:

    #user_db는 디비담당 레이어의 코드가 들어있음
    def __init__(self,user_dao,config,s3_client):
        self.user_dao = user_dao
        self.config = config

        #이 코드의 경우 의존성(객체)를 내부에서 받는다 -> 좋지 않음
        # self.s3 = boto3.client("s3",aws_access_key_id = config['S3_ACCESS_KEY'],aws_secret_access_key = config['S3_SECRET_KEY'])

        #의존성을 외부에서 주입받도록 해준다.
        self.s3 = s3_client

    #유저 생성하는 로직
    def create_new_user(self,new_user):
        new_user['password'] = bcrypt.hashpw(new_user['password'].encode('UTF-8'),bcrypt.gensalt())

        new_user_id = self.user_dao.insert_user(new_user)

        return new_user_id

    #로그인 로직
    def login(self, credential):
        email = credential['email']
        password = credential['password']

        #디비에 접속하는 로직 - id과 해쉬화 된 비밀번호가 리턴됨
        user_credential= self.user_dao.get_user_id_passwd(email)

        #디비조회시 없으면 None이 리턴되어서 and를 했을때 None이 들어감
        authorized = bcrypt.checkpw(password.encode('UTF-8'),user_credential['hashed_password'].encode('UTF-8'))
        
        return authorized

    #유저 id와 패스워드 가져오기
    def get_user_id_passwd(self,email):
        return self.user_dao.get_user_id_passwd(email)

    #토큰 발급해주는 로직
    def generate_access_token(self,user_id):
        payload = {
                    "user_id":user_id,
                    "exp":datetime.utcnow()+timedelta(seconds=self.config['JWT_EXP_DELTA_SECOND'])
                }
        
        token = jwt.encode(payload,self.config['JWT_SECRET_KEY'],'HS256')

        return token

    #팔로우 하기
    def follow(self,payload):
        # user_id = payload['id']
        # follow_id = payload['follow'] 

        # return self.user_dao.insert_follow(user_id,follow_id)
        return self.user_dao.insert_follow(payload)
    
    #팔로우 취소
    def unfollow(self,payload):
        # user_id = payload['id']
        # unfollow_id = payload['follow']

        # return self.user_dao.insert_unfollow(user_id,unfollow_id)
        return self.user_dao.insert_unfollow(payload)

    #파일저장
    def save_profile_picture(self,profile_picture,filename,user_id):
        # profile_picture_path = os.path.join(self.config['UPLOAD_DIRECTORY'],filename)
        # profile_picture.save(profile_picture_path)

        #aws s3에 파일 저장
        self.s3.upload_fileobj(profile_picture,self.config['S3_BUCKET'],filename)

        #aws s3에 저장된 경로
        image_url = f"{self.config['S3_BUCKET_URL']}{filename}"

        return self.user_dao.save_profile_picture(image_url,user_id)

    #파일 가져오기
    def get_profile_picture(self,user_id):
        return self.user_dao.get_profile_picture(user_id)