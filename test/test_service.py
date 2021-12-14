import bcrypt
import pytest
import config
import jwt

from models import TweetDao,UserDao
from service import TweetService,UserService
from sqlalchemy import create_engine,or_,text
from sqlalchemy.orm import session, sessionmaker
from models.model import User,Tweet,UsersFollowList
from unittest import mock


database = create_engine(config.test_config['DB_URL'],encoding = 'utf-8',max_overflow=0)

@pytest.fixture
def user_service():
    mock_s3_client = mock.Mock()
    return UserService(UserDao(database),config.test_config, mock_s3_client)

@pytest.fixture
def tweet_service():
    return TweetService(TweetDao(database))

def setup_function():
    #테스트를 위한 유저 생성
    hashed_password = bcrypt.hashpw(b"test passwd",bcrypt.gensalt())

    new_users=[{
        'id':1,
        'name':'lee1',
        'email':'asdf1@asdf.com',
        'profile':'hello world1!',
        'password':hashed_password
    },
    {
        'id':2,
        'name':'lee2',
        'email':'asdf2@asdf.com',
        'profile':'hello world2!',
        'password':hashed_password
    }]

    Session = sessionmaker(bind=database)
    session = Session()

    for new_user in new_users:
        user_info = User(id=new_user['id'],name=new_user['name'],email=new_user['email'],hashed_password=new_user['password'],profile=new_user['profile'])
        session.add(user_info)

    user2_tweet_info = Tweet(user_id=2,tweet="hello world!")
    session.add(user2_tweet_info)
    session.commit()
    session.close()

def teardown_function():
    #테이블 삭제를 위해 외래키를 잠시 끔
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE TABLE users"))
    database.execute(text("TRUNCATE TABLE tweets"))
    database.execute(text("TRUNCATE TABLE users_follow_list"))
    #다시 외래키를 킴
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    # database.execute(text("ALTER TABLE users AUTO_INCREMENT=1"))

#유저 가져오기
def get_user(user_id):
    Session = sessionmaker(bind=database)
    session = Session()

    user_info = session.query(User.id,User.name,User.email,User.profile).filter(User.id==user_id).first()

    return_result = dict()

    if user_info is not None:
        return_result['id'] = user_info[0]
        return_result['name'] = user_info[1]
        return_result['email'] = user_info[2]
        return_result['profile'] = user_info[3]

    session.close()
    return return_result

#팔로우 리스트 가져오기
def get_follow_list(user_id):
    Session = sessionmaker(bind=database)
    session = Session()

    follow_list = session.query(UsersFollowList.follow_user_id).filter(UsersFollowList.user_id==user_id).all()

    return_result = list()
    session.close()
    for follow in follow_list:
        return_result.append(follow[0])

    return return_result

#유저 생성 테스트
def test_create_new_user(user_service):
    new_user = {
        'name':'lee3',
        'email':'asdf3@asdf.com',
        'profile':'hello world3!',
        'password':'test1234'

    }

    new_user_id = user_service.create_new_user(new_user)
    created_user = get_user(new_user_id)

    assert created_user == {
        'id': new_user_id,
        'name':new_user['name'],
        'email':new_user['email'],
        'profile':new_user['profile']
    } 

def test_login(user_service):
    #이미 생성된 계정으로 로그인 시도
    #assert가 None이면 에러가 남
    #이미 생성정의 경우 None이 아님
    correct_credential = {
        'email':'asdf1@asdf.com',
        'password':'test passwd'
    }
    assert user_service.login(correct_credential)

    #잘못된 정보로 로그인 시도 - None이 리턴되어 AssertionError가 남
    incorrect_credential = {
        'email':'asdf1@asdf.com',
        'password':'test1234'
    }
    #None이거나 False면 assertionError
    assert not user_service.login(incorrect_credential)

#토큰 확인 테스트
def test_generate_access_token(user_service):
    #토큰 생성후에 decode했을때 동일한 사용자 id가 나오는지 확인
    token = user_service.generate_access_token(1)
    payload = jwt.decode(token,config.JWT_SECRET_KEY,'HS256')

    assert payload['user_id']==1

#팔로우 테스트
def test_follow(user_service):
    payload = {
        'id':1,
        'follow':2
    }
    user_service.follow(payload)

    follow_list = get_follow_list(1)

    assert follow_list == [2]

def test_unfollow(user_service):
    payload = {
        'id':1,
        'unfollow':2
    }
    user_service.follow(payload)
    user_service.unfollow(payload)
    follow_list = get_follow_list(1)

    assert follow_list == []

#트윗 테스트
def test_tweet(tweet_service):
    paylaod = {
        'id':1,
        'tweet':"tweet test"
    }
    tweet_service.insert_tweet(paylaod)
    timeline = tweet_service.get_timeline(1)

    #트윗이 제대로 되었는지 확인
    assert timeline == [
        {
            'user_id':1,
            'tweet':'tweet test'
        }
    ]
#타임라인 테스트
def test_timeline(user_service,tweet_service):
    payload1 = {
        'id':1,
        'tweet': 'tweet test'
    }
    payload2 = {
        'id':2,
        'tweet': 'tweet test2'
    }
    tweet_service.insert_tweet(payload1)
    tweet_service.insert_tweet(payload2)

    follow_payload = {
        'id':1,
        'follow':2
    }
    #1번에서 2번 팔로우
    user_service.follow(follow_payload)

    timeline = tweet_service.get_timeline(1)


    assert timeline == [
        {
            'user_id':2,
            'tweet':'hello world!',
        },
        {
            'user_id':1,
            'tweet':'tweet test'
        },
        {
            'user_id':2,
            'tweet': 'tweet test2'
        }
    ]


#이미지 저장 테스트
def test_save_get_profile_picture(user_service):
    #이미지 먼저 읽어들이기
    #없으면 None이 나옴
    user_id = 1
    user_profile_picture = user_service.get_profile_picture(user_id)
    assert user_profile_picture is None

    #이미지 경로 저장
    test_picture = mock.Mock()
    filename = "test.png"
    user_service.save_profile_picture(test_picture,filename,user_id)

    #이미지 들이기
    actual_profile_picture = user_service.get_profile_picture(user_id)
    assert actual_profile_picture == "http://s3.ap-northeast-2.amazonaws.com/test/test.png"

    