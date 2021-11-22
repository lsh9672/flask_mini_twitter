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
    #테스트 유저 생성
    hashed_password1 = bcrypt.hashpw(
        b'1234',
        bcrypt.gensalt()
    )
    hashed_password2 = bcrypt.hashpw(
        b'12345',
        bcrypt.gensalt()
    )
    new_test_user1 = {
        'id':1,
        'name':'lee',
        'email':'asdf@asdf.com',
        'profile':'hello world!',
        'hashed_password':hashed_password1
    }
    new_test_user2 = {
        'id':2,
        'name':'lee2',
        'email':'asdf2@asdf2.com',
        'profile':'hello world!',
        'hashed_password':hashed_password2
    }
    Session = sessionmaker(bind=database)
    session = Session()
    test_user_info1 = User(id=new_test_user1['id'],name=new_test_user1['name'],email=new_test_user1['email'],hashed_password=new_test_user1['hashed_password'],profile=new_test_user1['profile'])
    test_user_info2 = User(id=new_test_user2['id'],name=new_test_user2['name'],email=new_test_user2['email'],hashed_password=new_test_user2['hashed_password'],profile=new_test_user2['profile'])
    user2_tweet_info = Tweet(user_id=2,tweet="hello world!")
    session.add(test_user_info1)
    session.add(test_user_info2)
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
    resp = api.post('/login', data = json.dumps({'email':'asdf@asdf.com',"password":"1234"}), content_type='application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))

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
    resp = api.post('/login',data=json.dumps({"email":"asdf@asdf.com","password":"1234"}), content_type = 'application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']


    # 트윗하기
    resp = api.post('/tweet', data = json.dumps({'tweet':'hello world!'}),content_type = 'application/json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    # 타임라인 확인
    resp = api.get(f'/timeline2/1',headers = {'Authorization': access_token})
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
    resp = api.post('login', data = json.dumps({"email":"asdf@asdf.com","password":"1234"}),content_type = 'application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    #1번 사용자의 트윗 리스트가 비어있는것을 확인
    resp = api.get('/timeline2/1',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline':[]
    }

    #사용자 아이디 2 follow
    resp = api.post('/follow', data = json.dumps({"follow":2}),content_type = 'application.json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    #1의 timeline을 확인해서 2의 값이 나오는지 확인

    resp = api.get('/timeline2/1',headers = {'Authorization': access_token})
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
def test_follow(api):
    #로그인
    resp = api.post('login', data = json.dumps({"email":"asdf@asdf.com","password":"1234"}),content_type = 'application/json')
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    #follow사용자 아이디 = 2
    resp = api.post('/follow', data = json.dumps({'follow':2}),content_type = 'application/json',headers = {'Authorization': access_token})
    assert resp.status_code == 200

    #1의 트윗을 확인해서 2가 안나오는 것을 확인
    resp = api.get('/timeline2/1',headers = {'Authorization': access_token})
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
    resp = api.get('timeline2/1',headers = {'Authorization': access_token})
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline':[]
    }
