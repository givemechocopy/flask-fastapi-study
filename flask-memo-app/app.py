"""
SQLALCHEMY_DATABASE_URI는 MySQL 데이터베이스에 연결하는 데 필요한 정보를 포함한다.
- username : 사용자 이름
- password : 비밀번호
- localhost : 호스트 주소
- my_memo_app : 데이터베이스 이름
"""
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os


app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'      # 로그인 페이지의 뷰 함수 이름


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
# SQLAlchemy의 수정 추적 기능을 비활성화 (성능 상의 이유)
app.config['SQLALCHEMY_TRACK)MODIFICATIONS'] = False
# 세션 및 쿠키에 대한 보안 향상을 위한 필요한 비밀 키 설정
app.config['SECRET_KEY'] = 'mysecretkey'
db = SQLAlchemy(app)


# 데이터 모델 정의
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))       # 사용자 참조 추가

    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return f'<Memo {self.title}>'

# 사용자 모델을 정의하고 데이터베이스 스키마에 반영
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 기존 라우트
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return '이것은 마이 메모 앱의 소개 페이지입니다.'


# 데이터베이스 생성
with app.app_context():
    db.create_all()


# 메모 생성
@app.route('/memos/create', methods=['POST'])
@login_required
def create_memo():
    title = request.json['title']
    content = request.json['content']
    new_memo = Memo(user_id=current_user.id, title=title, content=content)  # 현재 로그인한 사용자의 ID 추가
    db.session.add(new_memo)
    db.session.commit()
    return jsonify({'message': 'Memo created'}), 201


# 메모 조회
@app.route('/memos', methods=['GET'])
def list_memos():
    memos = Memo.query.filter_by(user_id=current_user.id).all()           # 현재 로그인한 사용자의 메모만 조회
    return render_template('memos.html',
                           memos=memos, username=current_user.username)   # 사용자별 메모를 표시하는 템플릿 렌더링


# 메모 업데이트
@app.route('/memos/update/<int:id>', methods=['PUT'])
def update_memo(id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()     # 현재 사용자의 메모만 선택
    if memo:
        memo.title = request.json['title']
        memo.content = request.json['content']
        db.session.commit()
        return jsonify({'message': 'Memo updated'}), 200
    else:
        abort(404, descrption="Memo not found or not authorized")


# 메모 삭제
@app.route('/memos/delete/<int:id>', methods=['DELETE'])
def delete_memo(id):
    memo = Memo.query.filter_by(id=id, uUser_id=current_user.id).first()     # 현재 사용자의 메모만 선택
    if memo:
        db.session.delete(memo)
        db.session.commit()
        return jsonify({'message': 'Memo deleted'}), 200
    else:
        abort(404, description="Memo not found or not authorized")


# Flask-Login이 현재 로그인한 사용자를 로드할 수 있도록 사용자 로딩 함수 정의
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return jsonify({'message': 'Logged in successfully'}), 200
        return abort(401, description="Invalid credentials")
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home')) # 로그아웃 후 메인 페이지로 리다이렉트


# 새로운 사용자가 시스템에 등록을 위한 회원가입 기능 추가
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # 회원가입 실패시 에러 메시지를 JSON 형태로 반환 (프론트엔드 페이지에서 해당 메세지를 기반으로 팝업을 띄움)
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return jsonify({'error': '사용자 이름 또는 이메일이 이미 사용 중입니다.'}), 400

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({'message': '회원가입이 성공하였습니다. 기입한 아이디와 패스워드로 로그인할 수 있습니다.'}), 201
    return redirect(url_for('home')) # 비정상요청의 경우 인 페이지로 리다이렉트
