from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
import config
from models import TweetDao,UserDao
from service import TweetService,UserService
from view import create_endpoints
import boto3


#service클래스들을 담고 있을 클래스
class Services:
    pass

#app 파일에서 각 레이어들을 이어주는 역할을 한다.
#생성자를 통해서 필요한 의존관계를 주입해준다.
def create_app(test_config = None):
    app = Flask(__name__)

    CORS(app)

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'],encoding = 'utf-8',max_overflow = 0)

    ##Persistence Layer
    user_dao = UserDao(database)
    tweet_dao = TweetDao(database)

    #Business Layer

    s3_client = boto3.client("s3",aws_access_key_id = app.config['S3_ACCESS_KEY'],aws_secret_access_key = app.config['S3_SECRET_KEY'])

    service = Services
    service.user_service = UserService(user_dao,app.config,s3_client)
    service.tweet_service = TweetService(tweet_dao)

    ##엔드포인트들 생성
    create_endpoints(app,service)

    return app
