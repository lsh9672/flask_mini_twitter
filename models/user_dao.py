from re import L
from sqlalchemy.orm import session, sessionmaker
from .model import User,Tweet,UsersFollowList


#유저관련 디비
class UserDao:
    def __init__(self,database):
        self.db = database
    
    #디비 회원정보 넣기
    def insert_user(self,new_user):
        Session = sessionmaker(bind=self.db)
        session = Session()

        #new user data insert
        try:
            user_info = User(name=new_user['name'],email=new_user['email'],profile=new_user['profile'],hashed_password=new_user['password'])
            session.add(user_info)
            session.commit()
        except:
            session.close()
            return None

        new_user_id = user_info.id
        session.close()

        return new_user_id

    #디비 유저 조회
    def get_user_id_passwd(self,email):
        Session = sessionmaker(bind=self.db)
        session = Session()

        try:
            #user_id,password
            user_info = session.query(User.id,User.hashed_password).filter(User.email==email).first()
        except:
            session.close()
            return None

        session.close()
        return_result = dict()
        
        if user_info:
            return_result = {"id":user_info[0],"hashed_password":user_info[1]}
            return return_result
        else:
            return None

    #디비 팔로우데이터 넣기
    def insert_follow(self,payload):
        Session = sessionmaker(bind = self.db)
        session = Session()
        try:
            follow_info = UsersFollowList(user_id=payload['id'],follow_user_id = payload['follow'])
            session.add(follow_info)
            session.commit()
        except:
            session.close()
            return None

        session.close()
        return "success"

    #디비 팔로우 삭제
    def insert_unfollow(self,payload):
        Session = sessionmaker(bind = self.db)
        session = Session()
        try:
            unfollow_info = session.query(UsersFollowList).filter(UsersFollowList.user_id == payload['id'],UsersFollowList.follow_user_id == payload['unfollow']).first()
            session.delete(unfollow_info)
            session.commit()
        except:
            session.close()
            return None

        session.close()
        return "success"
    
    #디비에 프로파일 이미지 경로 저장
    def save_profile_picture(self,profile_picture_path,user_id):
        Session = sessionmaker(bind = self.db)
        session = Session()

        try:
            update_info = session.query(User).filter(User.id == user_id).update({'profile_picture':profile_picture_path})
            session.commit()
        except:
            session.close()
            return None

        session.commit()
        return update_info

    #디비에서 경로를 가져와서 리턴
    def get_profile_picture(self,user_id):

        Session = sessionmaker(bind=self.db)
        session = Session()

        try:
            image_path = session.query(User.profile_picture).filter(User.id == user_id).first()
        except:
            session.close()
            return None

        session.close()

        if image_path is not None: 
            return image_path[0]
            
        else: 
            None