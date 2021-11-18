# 트위터의 일부 기능을 구현해보는 rest api 서버(2021.11.08~)

> ### 환경

- os: ubuntu 20.04.3LTS
- python : 3.8.10,(flaks == 2.0.2)
- DB : mysql 8.0.27

- 참고 : 깔끔한 파이썬 탄탄한 백엔드 (저자: 송은우)

> ### 1일차(v 0.1)

- #### mysql을 이용하여 3개의 테이블 생성

  1. users: 유저 정보를 저장
  2. tweets : 유저별 트윗 내용 저장
  3. users_follow_list : 각 유저간 팔로우 내용 저장

- #### sqlacodegen을 이용하여 ORM 클래스를 생성

- #### 회원가입과 300자 이내의 글을 쓸수 있는 트위터 엔드포인트를 작성

> ### 2일차(v 0.2)

- #### timeline 엔드포인트를 작성

  1. join연산을 이용하여 자신의 트윗과 팔로우한 사용자의 트윗을 전부 조회해서 json으로 반환

- #### ORM을 통해 쿼리하는 로직을 따로 함수로 분리
  1. 사용자의 정보조회하는 로직 분리
  2. 회원가입시, DB에 insert하는 로직 분리

> ### 3일차(v 0.3)

- #### follow,unfollow 엔드 포인트 작성

  1. 유저 id 값과 follow 할 상대 id값을 받아서 디비에 추가함.
  2. 유저 id 값과 unfollow 할 상대의 id 값을 받아서 디비에서 삭제함.

- #### ORM을 통해 쿼리하는 로직을 따로 함수로 분리
  1. follow 시에 insert하는 로직을 따로 분리
  2. unfollow 시에 delete하는 로직을 따로 분리
  3. timeline출력시에 join연산하는 로직을 따로 분리

> ### 4일차(v 0.4)

- #### 비밀번호에 암호화 적용 및 로그인 기능 추가(JWT 토큰방식)

  1. 기존에 입력된 그대로 저장되던 비밀번호에 bcrypt암호화 알고리즘을 적용해서 암호화하는 함수 작성
  2. 입력받은 이메일과 비밀번호를 받고, 비밀번호는 암호화하고 이메일을 이용해서 데이터베이스에 저장된 암호화된 비밀번호를 가져온후 이 두개를 비교하여 같으면 JWT토큰을 발행함

- #### 회원인증 데코레이터 함수 추가
  1. 로그인이 필요한 기능(엔드포인트)에는 JWT를 받아서 유효한 토큰일 경우에만 사용할수 있도록 하는 로직이 담긴 데코레이터 함수를 만듦
  2. 데코레이터 함수를 로그인이 필요한기능(트윗,팔로우,언팔로우)에 추가함
