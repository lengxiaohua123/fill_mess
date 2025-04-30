from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {'lengxiaohua123': {'password': 'test123'}}

# 模拟数据库
current_time = "2025-04-30 09:28:32"  # 使用当前时间
drugs_data = [
    {
        'id': 1,
        'drug_name': '琥珀安神丸',
        'specification': '3ml:300IU/瓶提纯剂/支/盒',
        'update_time': current_time,
        'operator': 'lengxiaohua123',
        'status': '启用'
    },
    {
        'id': 2,
        'drug_name': '牡蛎丸',
        'specification': '10g:0.1g/支/盒',
        'update_time': current_time,
        'operator': 'lengxiaohua123',
        'status': '启用'
    },
    {
        'id': 3,
        'drug_name': '维生素B12片',
        'specification': '25μg*100片/瓶',
        'update_time': current_time,
        'operator': 'lengxiaohua123',
        'status': '启用'
    }
]

@login_manager.user_loader
def load_user(user_id):
    if user_id not in users:
        return None
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('drug_dictionary'))
        flash('用户名或密码错误')
    return render_template('login.html')

# 添加登出路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/drug_dictionary')
@login_required
def drug_dictionary():
    return render_template('drug_dictionary.html', drugs=drugs_data)

@app.route('/api/drug', methods=['POST'])
@login_required
def add_drug():
    data = request.json
    new_drug = {
        'id': len(drugs_data) + 1,
        'drug_name': data['drug_name'],
        'specification': data['specification'],
        'update_time': current_time,
        'operator': current_user.id,
        'status': '启用'
    }
    drugs_data.append(new_drug)
    return jsonify({'success': True, 'drug': new_drug})

@app.route('/api/drug/<int:id>', methods=['PUT'])
@login_required
def update_drug(id):
    data = request.json
    for drug in drugs_data:
        if drug['id'] == id:
            drug['drug_name'] = data['drug_name']
            drug['specification'] = data['specification']
            drug['update_time'] = current_time
            drug['operator'] = current_user.id
            return jsonify({'success': True, 'drug': drug})
    return jsonify({'success': False, 'message': 'Drug not found'}), 404

@app.route('/api/drug/status/<int:id>', methods=['PUT'])
@login_required
def toggle_status(id):
    for drug in drugs_data:
        if drug['id'] == id:
            drug['status'] = '停用' if drug['status'] == '启用' else '启用'
            drug['update_time'] = current_time
            drug['operator'] = current_user.id
            return jsonify({'success': True, 'drug': drug})
    return jsonify({'success': False, 'message': 'Drug not found'}), 404

@app.route('/api/search', methods=['POST'])
@login_required
def search_drugs():
    data = request.json
    
    drug_search = data.get('drug_search', '').lower()
    date_from = data.get('date_from')
    date_to = data.get('date_to')
    operator = data.get('operator', '').lower()
    status = data.get('status')

    filtered_drugs = drugs_data.copy()

    if drug_search:
        filtered_drugs = [drug for drug in filtered_drugs 
                        if drug_search in drug['drug_name'].lower()]
    
    if date_from and date_to:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            filtered_drugs = [drug for drug in filtered_drugs 
                            if date_from <= datetime.strptime(drug['update_time'], '%Y-%m-%d %H:%M:%S') < date_to]
        except ValueError:
            pass

    if operator:
        filtered_drugs = [drug for drug in filtered_drugs 
                        if operator in drug['operator'].lower()]

    if status and status != 'all':
        status_map = {'enabled': '启用', 'disabled': '停用'}
        filtered_drugs = [drug for drug in filtered_drugs 
                        if drug['status'] == status_map.get(status, drug['status'])]

    return jsonify({'success': True, 'drugs': filtered_drugs})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
