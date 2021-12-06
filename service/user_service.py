import bcrypt
from datetime import datetime, timedelta
import jwt


#비즈니스 로직 - 실질적으로 유저를 추가하고 트윗을 추가하는 등의 로직이 들어감
#UserService에는 사용자생성, 팔로우, 언팔로우 등의 사용자 관련된 로직이 들어감.
class UserService:

    #user_db는 디비담당 레이어의 코드가 들어있음
    def __init__(self,user_dao,config):
        self.user_dao = user_dao
        self.config = config

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
                    "exp":datetime.utcnow()+timedelta(seconds=60*60*24)
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