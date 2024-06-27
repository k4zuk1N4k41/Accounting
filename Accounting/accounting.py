#-----------------------------------------------------
# インポート
#-----------------------------------------------------
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required

from werkzeug.security import generate_password_hash, check_password_hash
import os

#-----------------------------------------------------
# 前処理
#-----------------------------------------------------
accounting = Flask(__name__)

#データベースのURIの設定
accounting.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounting.db'
#セッションやパスワードを暗号化するためのKeyを作成
accounting.config['SECRET_KEY'] = os.urandom(24)

#SQLAlchemyのインスタンスを作成
db = SQLAlchemy(accounting)

#login_Managerの作成
login_Manager = LoginManager()
#依存関係の設定
login_Manager.init_app(accounting)


@login_Manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#テータベース初期化の関数
def initialize_database():
    #アプリケーションコンテキストを作成してデータベースのテーブルを作成
    with accounting.app_context():
        db.create_all()

#-----------------------------------------------------
# データベースのテーブル定義
#-----------------------------------------------------
#Userモデルを定義
class User(UserMixin ,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(12))
#Roomモデルを定義
class Room(UserMixin ,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(30))
    roomname = db.Column(db.String(30), unique=True)
#Accountingモデルを定義
class Accounting(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roomname = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(30), nullable=False)
    money = db.Column(db.Integer, nullable=False, default=0)
#-----------------------------------------------------
# ログイン処理
#-----------------------------------------------------
@accounting.route('/', methods=['GET','POST'])
def signup():
    #遷移するhtmlを管理する
    html = 'login.html'
    
    if request.method == 'POST':
        #次の画面に送るテキストを保持
        msg = ''
        #遷移するhtmlを管理する
        html = 'login.html'
        #押されたボタンの値を受け取る
        btn = request.form.get('btn')
        
        #登録ボタンが押されたら
        if btn == '登録':
            
            #form送信されてきた情報を受け取る
            username = request.form.get('username')
            password = request.form.get('password')
            
            #名前で検索をかける
            user = User.query.filter_by(username=username).first()
            
            if user is None:
            #Postクラスをインスタンス化
                user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
                msg = '登録に成功しました！'
                #DBへ登録
                db.session.add(user)
                db.session.commit()
            else:
                msg = '登録に失敗しました！'
        else:
             #form送信されてきた情報を受け取る
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            #該当するユーザー名がある場合
            if user is not None:
                #パスワードが正しい場合
                if check_password_hash(user.password, password):
                    login_user(user)
                    html = 'room.html'
                    msg = username + 'さんようこそ'
                    rooms = Room.query.all()
                    return render_template(html, msg=msg, username=username, rooms=rooms)
                #パスワードが正しくない場合
                else:
                    msg = 'パスワードが間違っています'
            #該当するユーザー名がない場合
            else:
                msg = '登録情報がありません'
        #ページを戻す
        return render_template(html, msg=msg)        
    
    else:
        return render_template(html)

#-----------------------------------------------------
# ルーム機能
#-----------------------------------------------------
@accounting.route('/room', methods=['GET','POST'])
@login_required
def room():
    if request.method == 'POST':
        btn = request.form.get('btn')
        roomname = request.form.get('roomname')
        username = request.form.get('username')
        #作成ボタンが押された場合
        if btn == '作成':
            #Roomのインスタンス化
            room = Room(roomname=roomname, author=username)
            
            #Accountingのインスタンス化
            accounting = Accounting(roomname=roomname, username=username)
            
            #DBへ登録
            db.session.add(room)
            db.session.commit()
            
            db.session.add(accounting)
            db.session.commit()
            
            #htmlへ返すデータを用意
            user_infos = Accounting.query.all()
            
            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname) 
        elif btn == '検索':
            if roomname is not None:
                user_infos = Accounting.query.filter_by(roomname=roomname)
                for user_info in user_infos:
                    if user_info.username == username:
                        return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)
                    else:
                        if user_infos.count() >= 2:
                            msg = '部屋が満室です'
                            rooms = Room.query.all()
                            
                            return render_template('room.html', msg=msg, username=username, rooms=rooms)
                        else:
                            user_info = Accounting(username=username, roomname=roomname)
                            
                            db.session.add(user_info)
                            db.session.commit()
                            
                            user_infos = Accounting.query.filter_by(roomname=roomname)
                            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)
            else:
                rooms = Room.query.all()
                msg = 'ルーム名を入力してください'
                html = 'room.html'
                return render_template(html, msg=msg, username=username, rooms=rooms)          
        elif btn == '削除':
            print('roomname：'+ roomname)
            print('username：' + username)
            room = Room.query.filter_by(roomname=roomname).first()
            #作成者だった場合
            if room.author == username:
                db.session.delete(room)
                db.session.commit()
                
                #ルーム内の情報も削除する
                user_infos = Accounting.query.filter_by(roomname=roomname)
                for user_info in user_infos:  
                    db.session.delete(user_info)
                    db.session.commit()
                msg = '削除に成功しました'
            else:
                msg = '権限がありません'
            rooms = Room.query.all()
                
            return render_template('room.html', msg=msg, username=username, rooms=rooms)
    else:
        return render_template('room.html')

#-----------------------------------------------------
# ルーム分岐画面
#-----------------------------------------------------
@accounting.route('/roomInfo', methods=['GET','POST'])
@login_required
def roomInfo():
    if request.method == 'POST':
        btn = request.form.get('btn')
        username = request.form.get('username')
        roomname = request.form.get('roomname')
        if btn == '追加':            
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            return render_template('accounting.html', user_infos=user_infos, username=username, roomname=roomname)
        
        elif btn == '返済':
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            return render_template('repayment.html', user_infos=user_infos, username=username, roomname=roomname)
        
        elif btn == 'リセット':
            user_infos = Accounting.query.filter_by(roomname=roomname)
            for user_info in user_infos:
                user_info.money = 0
            db.session.commit()
            
            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)
        
        elif btn == '更新':
            user_infos = Accounting.query.filter_by(roomname=roomname)
        
            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)
        
        elif btn == '戻る':
            msg = username + 'さんようこそ'
            rooms = Room.query.all()
            
            return render_template('room.html', msg=msg, username=username, rooms=rooms)

#-----------------------------------------------------
# 会計情報追加画面
#-----------------------------------------------------
@accounting.route('/confirmation', methods=['GET','POST'])
@login_required
def confirmation():
    if request.method == 'POST':
        btn = request.form.get('btn')
        username = request.form.get('username')
        roomname = request.form.get('roomname')
        if btn == '追加':
            give_money = request.form.get('give_money')
            total = request.form.get('total')
            ratio = request.form.get('ratio')
            myself_total = request.form.get('myself_total')
            partner_total = request.form.get('partner_total')
            
            return render_template('confirmation.html', username=username, roomname=roomname, partner_total=partner_total, myself_total=myself_total, ratio=ratio, total=total, give_money=give_money)
        elif btn == '追加確定':
            give_money = request.form.get('give_money')
            total = (int)(request.form.get('total'))
            ratio = (float)(request.form.get('ratio'))/100
            myself_total = (int)(request.form.get('myself_total'))
            partner_total = (int)(request.form.get('partner_total'))
            print(total)
            print(ratio)
            print(myself_total)
            print(partner_total)
            #現在の会計状況
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            #追加する金額
            pull_money = (int)((total - (myself_total + partner_total)) * ratio)
            
            #支払ったのがログインユーザーの場合
            print(give_money)
            if give_money == username:
                
                for user_info in user_infos:
                    #ログインユーザーでない情報を更新する
                    print(user_info.username)
                    if user_info.username != username:
                        pull_money += partner_total
                        pull_money *= 1.08
                        after_money = (int)(user_info.money) - (int)(pull_money + 0.5)
                        user_info.money = after_money
                        db.session.commit()
                        break
            #支払ったのがログインユーザーではない場合
            else:
                for user_info in user_infos:
                    if user_info.username == username:
                        pull_money += myself_total
                        pull_money *= 1.08
                        print(pull_money)
                        after_money = (int)(user_info.money) - (int)(pull_money + 0.5)
                        after_money = (int)(user_info.money) - pull_money
                        user_info.money = after_money
                        print(after_money)
                        db.session.commit()
                        break
            user_infos = Accounting.query.filter_by(roomname=roomname)
            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)
        
        elif btn == '返済':
            give_money = request.form.get('give_money')
            total = request.form.get('total')
            
            return render_template('reconfirmation.html', roomname=roomname, username=username, give_money=give_money, total=total)

        elif btn == '返済確定':
            give_money = request.form.get('give_money')
            total = (int)(request.form.get('total'))
            
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            for user_info in user_infos:
                if user_info.username == give_money:
                    user_info.money = (int)(user_info.money) + total
                    db.session.commit()
                    break
            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)
        elif btn == '返済画面へ':
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            return render_template('repayment.html', user_infos=user_infos, username=username, roomname=roomname)
        elif btn == '追加画面へ':
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            return render_template('accounting.html', user_infos=user_infos, username=username, roomname=roomname)
        #戻るボタン
        else:
            user_infos = Accounting.query.filter_by(roomname=roomname)
            
            return render_template('roomInfo.html', user_infos=user_infos, username=username, roomname=roomname)

#-----------------------------------------------------
# ログアウト処理
#-----------------------------------------------------
@accounting.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')
#-----------------------------------------------------
# データベース作成
#-----------------------------------------------------
if __name__ == '__main__':
    initialize_database()  # データベースを初期化
    accounting.run(debug=True)