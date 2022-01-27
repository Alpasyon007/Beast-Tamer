from functools import wraps
from flask import Flask, render_template, request, Response, redirect, session, abort, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin
from flask_hashing import Hashing
import RPi.GPIO as GPIO
import time
from datetime import datetime
import psutil

app = Flask(__name__)

app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
hashing = Hashing(app)

class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = str(id)
        self.password = "SHA-256 PASSWORD HASH"
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)

Alp = User("Alp")

@login_manager.user_loader
def load_user(userid):
    return User(userid)

# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User(userid)

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == 'POST':
		password = request.form['password']
		user = load_user("Alp")
		h = hashing.hash_value(password)
		if h == user.password:
			login_user(user, remember=True)
			return redirect('/')
		else:
			return abort(401)
	else:
		return render_template('beast_login.html')

@app.route('/', methods=['POST', 'GET'])
@login_required
def beastcontroller():
    statusFile = open("status.txt", "r")
    beast_status = "Unknown"
    if(statusFile.read() == "False"):
        isWoke = False
    else:
        isWoke = True
    statusFile.close()

    # Get cpu statistics
    cpu = str(psutil.cpu_percent()) + '%'

    # Calculate memory information
    memory = psutil.virtual_memory()
    # Convert Bytes to MB (Bytes -> KB -> MB)
    available = round(memory.available/1024.0/1024.0,1)
    total = round(memory.total/1024.0/1024.0,1)
    mem_info = str(available) + 'MB / ' + str(total) + 'MB ( ' + str(memory.percent) + '% )'

    # Calculate disk information
    disk = psutil.disk_usage('/')
    # Convert Bytes to GB (Bytes -> KB -> MB -> GB)
    free = round(disk.free/1024.0/1024.0/1024.0,1)
    total = round(disk.total/1024.0/1024.0/1024.0,1)
    disk_info = str(free) + 'GB / ' + str(total) + 'GB ( ' + str(disk.percent) + '% )'

    status = request.form.get('submit')
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.OUT)      
    GPIO.setup(17, GPIO.OUT)      
    if status == 'Wake the Beast':
        statusFile = open("status.txt", "w")
        beast_status = "Beast is Awake"
        GPIO.output(4, 1)
        time.sleep(0.1)
        GPIO.output(4, 0)
        isWoke = True
        statusFile.write("True")
        statusFile.close()
    elif status == 'Kill the Beast':
        statusFile = open("status.txt", "w")
        beast_status = "Beast is Dead"
        GPIO.output(4, 1)
        time.sleep(4)
        GPIO.output(4, 0)
        isWoke = False
        statusFile.write("False")
        statusFile.close()
    elif status == 'Restart the Beast':
        print("RESTART")
        GPIO.output(17, 1)
        time.sleep(1)
        GPIO.output(17, 0)
    else:
        beast_status = "Unknown"
    return render_template('beast_tamer.html', beast_status = beast_status, isWoke = isWoke, datetime = datetime.now(), cpu = cpu, mem_info = mem_info, disk_info = disk_info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')