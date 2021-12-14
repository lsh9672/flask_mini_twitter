import bcrypt
import pytest
import config

from models import UserDao,TweetDao
from sqlalchemy import create_engine,or_,text
from sqlalchemy.orm import session, sessionmaker
from models.model import User,Tweet,UsersFollowList


database = create_engine(config.test_config['DB_URL'],encoding = 'utf-8',max_overflow=0)

#models부분의 user쪽 디비처리 테스트
@pytest.fixture
def user_dao():
    return UserDao(database)

#models부분의 tweet쪽 디비처리 테스트
@pytest.fixture
def tweet_dao():
    return TweetDao(database)

def setup_function():
    #테스트를 위한 유저 생성
    hashed_password = bcrypt.hashpw(b"test passwd",bcrypt.gensalt())

    new_users=[{
        'id':1,
        'name':'lee1',
        'email':'asdf1@asdf.com',
        'profile':'hello world1!',
        'password':hashed_password
    },{
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

def test_insert_user(user_dao):
    new_user = {
        'name':'testName',
        'email':'test@test.com',
        'profile':'test hello!',
        'password':'test1234'
    }

    new_user_id = user_dao.insert_user(new_user)
    user = get_user(new_user_id)

    assert user == {
        'id':new_user_id,
        'name':user['name'],
        'email':user['email'],
        'profile':user['profile']
    }

#id,password 테스트
def test_get_user_id_passwd(user_dao):
    user_credential = user_dao.get_user_id_passwd(email = "asdf1@asdf.com")

    #사용자 아이디가 맞는지 확인
    assert user_credential['id'] == 1

    #비밀번호가 맞는지 확인
    assert bcrypt.checkpw('test passwd'.encode('UTF-8'),user_credential['hashed_password'].encode('UTF-8'))

#팔로우 추가 확인
def test_insert_follow(user_dao):
    payload={
        'id':1,
        'follow':2
    }
    #리턴값이 있어서 변수에 잠시 넣어둠
    check =user_dao.insert_follow(payload)

    follow_list= get_follow_list(1)

    assert follow_list == [2]

#언팔로우 테스트
def test_insert_unfollow(user_dao):
    payload1={
        'id':1,
        'follow':2
    }
    #unfollow용도
    payload2={
        'id':1,
        'unfollow':2
    }
    check1 = user_dao.insert_follow(payload1)
    check2 = user_dao.insert_unfollow(payload2)

    follow_list = get_follow_list(1)

    assert follow_list == []

#트윗 테스트
def test_insert_tweet(tweet_dao):
    payload={
        'id':1,
        'tweet':'tweet test'
    }
    check = tweet_dao.insert_tweet(payload)
    timeline = tweet_dao.get_timeline(1)

    assert timeline == [
        {
        'user_id':1,
        'tweet':'tweet test'
        }
    ]

def test_timeline(user_dao,tweet_dao):
    payload1 = {
        'id':1,
        'tweet': 'tweet test'
    }
    payload2 = {
        'id':2,
        'tweet': 'tweet test2'
    }
    tweet_dao.insert_tweet(payload1)
    tweet_dao.insert_tweet(payload2)

    follow_payload = {
        'id':1,
        'follow':2
    }

    #1번에서 2번 팔로우
    user_dao.insert_follow(follow_payload)

    timeline = tweet_dao.get_timeline(user_id = 1)

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

#이미지 저장과 불러오기 테스트
def test_save_get_profile_picture(user_dao):
    #이미지를 읽어온다. - 처음에는 이미지가 없어서 None이 나옴
    user_id = 1
    user_profile_picture = user_dao.get_profile_picture(user_id)
    assert user_profile_picture is None

    #이미지를 저장한다
    expected_profile_picture = "http://miniter-api-bucket.s3.amazonaws.com/flask_miniter_ver1.png"
    user_dao.save_profile_picture(expected_profile_picture,user_id)

    #url읽어 들이기
    actual_profile_picture = user_dao.get_profile_picture(user_id)
    assert expected_profile_picture == actual_profile_picture


