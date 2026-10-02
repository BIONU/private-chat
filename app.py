<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>แอดมินแชท</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body { font-family: sans-serif; margin: 0; display: flex; height: 100vh; background: #f0f2f5; }
  #sidebar { width: 260px; background: #fff; border-right: 1px solid #ddd; overflow-y: auto; }
  #sidebar h3 { padding: 16px; margin: 0; background: #0084ff; color: #fff; }
  .friend { padding: 14px 16px; cursor: pointer; border-bottom: 1px solid #eee; }
  .friend:hover { background: #f5f5f5; }
  .friend.active { background: #e7f3ff; font-weight: bold; }
  #main { flex: 1; display: flex; flex-direction: column; background: #fff; }
  #header { padding: 14px 16px; background: #0084ff; color: #fff; font-weight: bold; }
  #messages { flex: 1; overflow-y: auto; padding: 12px; }
  .msg { margin: 6px 0; padding: 8px 12px; border-radius: 12px; max-width: 70%;
         word-wrap: break-word; }
  .me { background: #0084ff; color: #fff; margin-left: auto; }
  .them { background: #e4e6eb; color: #000; }
  .msg img { max-width: 100%; border-radius: 8px; display: block; margin-top: 4px; }
  #inputbar { display: flex; padding: 8px; border-top: 1px solid #ddd; gap: 6px;
              align-items: center; }
  #inputbar input[type=text] { flex: 1; padding: 10px; border: 1px solid #ccc;
                                border-radius: 20px; font-size: 15px; outline: none; }
  #inputbar button { padding: 10px 16px; border: 0; background: #0084ff; color: #fff;
                     border-radius: 20px; cursor: pointer; font-size: 15px; }
  #fileBtn { background: #e4e6eb; color: #333; padding: 10px 14px; border-radius: 50%;
             cursor: pointer; font-size: 18px; user-select: none; }
  #fileInput { display: none; }
  #inputbar input:disabled, #inputbar button:disabled { opacity: .5; cursor: not-allowed; }
</style>
</head>
<body>

<div id="sidebar">
  <h3>เพื่อนออนไลน์ (<span id="count">0</span>)</h3>
  <div id="friendList"></div>
</div>

<div id="main">
  <div id="header">เลือกเพื่อนทางซ้ายเพื่อเริ่มคุย</div>
  <div id="messages"></div>
  <div id="inputbar">
    <label id="fileBtn" for="fileInput">📎</label>
    <input id="fileInput" type="file" accept="image/*" disabled>
    <input id="msgInput" type="text" placeholder="พิมพ์ข้อความ..." disabled autocomplete="off">
    <button id="sendBtn" onclick="sendMsg()" disabled>ส่ง</button>
  </div>
</div>

<script>
const socket = io();
let curSid = null;
let curName = '';
const store = {};

socket.emit('admin_join');

socket.on('friend_list', list => {
  const box = document.getElementById('friendList');
  box.innerHTML = '';
  document.getElementById('count').textContent = list.length;
  list.forEach(f => {
    const div = document.createElement('div');
    div.className = 'friend' + (f.sid === curSid ? ' active' : '');
    div.textContent = f.name;
    div.onclick = () => selectFriend(f.sid, f.name);
    box.appendChild(div);
  });
});

socket.on('incoming', d => {
  if (!store[d.sid]) store[d.sid] = { name: d.name, msgs: [] };
  store[d.sid].msgs.push({ text: d.msg, cls: 'them', type: d.type || 'text' });
  if (curSid === d.sid) addMsg(d.msg, 'them', d.type || 'text');
  else {
    // ไฮไลต์เพื่อนที่ส่งข้อความมาใหม่
    const items = document.querySelectorAll('.friend');
    items.forEach(el => { if (el.textContent === d.name) el.style.fontWeight = 'bold'; });
  }
});

function selectFriend(sid, name) {
  curSid = sid; curName = name;
  document.getElementById('header').textContent = '💬 ' + name;
  document.getElementById('msgInput').disabled = false;
  document.getElementById('sendBtn').disabled = false;
  document.getElementById('fileInput').disabled = false;
  const box = document.getElementById('messages');
  box.innerHTML = '';
  (store[sid]?.msgs || []).forEach(m => addMsg(m.text, m.cls, m.type));
  document.querySelectorAll('.friend').forEach(el => {
    el.classList.toggle('active', el.textContent === name);
    if (el.textContent === name) el.style.fontWeight = 'normal';
  });
  document.getElementById('msgInput').focus();
}

function addMsg(content, cls, type = 'text') {
  const box = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  if (type === 'image') {
    const img = document.createElement('img');
    img.src = content;
    div.appendChild(img);
  } else {
    div.textContent = content;
  }
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function sendMsg() {
  if (!curSid) return;
  const input = document.getElementById('msgInput');
  const msg = input.value.trim();
  if (!msg) return;
  socket.emit('admin_message', { sid: curSid, msg, type: 'text' });
  addMsg(msg, 'me', 'text');
  if (!store[curSid]) store[curSid] = { name: curName, msgs: [] };
  store[curSid].msgs.push({ text: msg, cls: 'me', type: 'text' });
  input.value = '';
  input.focus();
}

document.getElementById('fileInput').addEventListener('change', function() {
  if (!curSid) return;
  const file = this.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    alert('รูปใหญ่เกินไป (สูงสุด 5 MB)');
    this.value = '';
    return;
  }
  const sid = curSid;
  const reader = new FileReader();
  reader.onload = function(e) {
    const dataUrl = e.target.result;
    socket.emit('admin_message', { sid, msg: dataUrl, type: 'image' });
    addMsg(dataUrl, 'me', 'image');
    if (!store[sid]) store[sid] = { name: curName, msgs: [] };
    store[sid].msgs.push({ text: dataUrl, cls: 'me', type: 'image' });
  };
  reader.readAsDataURL(file);
  this.value = '';
});

document.getElementById('msgInput').addEventListener('keypress', e => {
  if (e.key === 'Enter') sendMsg();
});
</script>
</body>
</html>
