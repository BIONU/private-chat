import os
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'mysecret123')

friends = {}  # {sid: {"name": str}}


def friend_list_with_sid():
    return [{"sid": sid, "name": info["name"]} for sid, info in friends.items()]


@app.route('/')
def index():
    return render_template('friend.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        return "รหัสผ่านผิด", 403

    if not session.get('is_admin'):
        return '''
        <html><body style="font-family:sans-serif;text-align:center;margin-top:80px">
        <h2>เข้าสู่หน้าแอดมิน</h2>
        <form method="post">
          <input type="password" name="password" placeholder="รหัสผ่าน"
                 style="padding:10px;font-size:16px">
          <button style="padding:10px 20px;font-size:16px">เข้า</button>
        </form></body></html>
        '''

    return render_template('admin.html')


@socketio.on('friend_join')
def on_friend_join(data):
    name = (data.get('name') or '').strip()[:30] or 'ไม่ระบุชื่อ'
    friends[request.sid] = {"name": name}
    join_room('friends')
    emit('friend_list', friend_list_with_sid(), to='admin')
    emit('system', {'msg': f'ยินดีต้อนรับ {name}'}, to=request.sid)


@socketio.on('admin_join')
def on_admin_join():
    join_room('admin')
    emit('friend_list', friend_list_with_sid())


@socketio.on('friend_message')
def on_friend_message(data):
    sid = request.sid
    info = friends.get(sid)
    if not info:
        return
    emit('incoming', {
        'sid': sid,
        'name': info['name'],
        'msg': data.get('msg', '')
    }, to='admin')


@socketio.on('admin_message')
def on_admin_message(data):
    target_sid = data.get('sid')
    msg = data.get('msg', '')
    if target_sid in friends:
        emit('from_admin', {'msg': msg}, to=target_sid)


@socketio.on('disconnect')
def on_disconnect():
    info = friends.pop(request.sid, None)
    if info:
        emit('friend_list', friend_list_with_sid(), to='admin')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
