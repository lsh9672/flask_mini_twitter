from sqlalchemy.orm.session import sessionmaker
from models.model import User,Tweet,UsersFollowList
from app import create_app
from sqlalchemy import create_engine,or_,text
import config
import pytest
import json
import bcrypt


database = create_engine(config.test_config['DB_URL'],encoding = 'utf-8',max_overflow = 0)

@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config['TEST'] = True
    api=app.test_client()


    return api

#테스트 코드 실행전 셋팅(디비초기화등)을 하기 위해 먼저 실행될 코드들
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

#테스트가 종료된 후 생성된 테스트 데이터를 제거하기 위한 코드들 - 테스트가 종료된 후 실행됨
def teardown_function():
    #테이블 삭제를 위해 외래키를 잠시 끔
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE TABLE users"))
    database.execute(text("TRUNCATE TABLE tweets"))
    database.execute(text("TRUNCATE TABLE users_follow_list"))
    #다시 외래키를 킴
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    # database.execute(text("ALTER TABLE users AUTO_INCREMENT=1"))

def test_ping(api):
    resp = api.get('/ping')
    assert b'pong' in resp.data

def test_login(api):
    resp = api.post('/login', data = json.dumps({'email':'asdf1@asdf.com',"password":"test passwd"}), content_type='application/json')
    
    assert b"access_token" in resp.data

def test_unauthorized(api):
    #access token 없이 접속시에 401 응답이 오는지 확인
    resp = api.post('/tweet',data = json.dumps({'tweet':'Hello World!'}),content_type = 'application/json')
    assert resp.status_code == 401

    resp = api.post('/follow', data = json.dumps({"follow":2}),content_type = 'application/json')
    assert resp.status_code == 401

    resp = api.post('/unfollow', data = json.dumps({"unfollow":2}), content_type = 'application/json')
    assert resp.status_code == 401

def test_tweet(api):
    #로그인 하기
    resp = api.post('/login',data=json.dumps({"email":"asdf1@asdf.com","password":"test passwd"}), content_type = 'application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']


    # 트윗하기
    resp = api.post('/tweet', data = json.dumps({'tweet':'hello world!'}),content_type = 'application/json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    # 타임라인 확인
    resp = api.get(f'/timeline',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200

    assert tweets == {
        'user_id':1,
        'timeline':[
            {
                "user_id":1,
                "tweet":"hello world!"
            }
        ]
    }

def test_follow(api):
    #로그인 과정
    resp = api.post('login', data = json.dumps({"email":"asdf1@asdf.com","password":"test passwd"}),content_type = 'application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    #1번 사용자의 트윗 리스트가 비어있는것을 확인
    resp = api.get('/timeline',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline':[]
    }

    #사용자 아이디 2 follow
    resp = api.post('/follow', data = json.dumps({"follow":2}),content_type = 'application/json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    #1의 timeline을 확인해서 2의 값이 나오는지 확인

    resp = api.get('/timeline',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline':[
            {
                'user_id':2,
                'tweet':'hello world!'
            }
        ]
    }

#unfollow
def test_unfollow(api):
    #로그인
    resp = api.post('login', data = json.dumps({"email":"asdf1@asdf.com","password":"test passwd"}),content_type = 'application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    #follow사용자 아이디 = 2
    resp = api.post('/follow', data = json.dumps({'follow':2}),content_type = 'application/json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    #1의 트윗을 확인해서 2가 안나오는 것을 확인
    resp = api.get('/timeline',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline':[
            {
                'user_id':2,
                'tweet':'hello world!'
            }
        ]
    }

    #unfollow 사용자 아이디 2
    resp = api.post('/unfollow', data = json.dumps({'unfollow':2}),content_type='application/json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    #사용자 1의 타임라인을 확인해서 더이상 2의 트윗이 안보이는 지 확인
    resp = api.get('timeline',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline':[]
    }
