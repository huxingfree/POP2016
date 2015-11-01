#from threading import Timer
from flask import *
from log_util import *
import urllib2
import urllib
__author__ = 'Hu Xing'

app = Flask(__name__)


# interface for editor to get app log
@app.route("/applog", methods=['GET','POST'])
def app_log():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    token = params.get('token', default=None)
    owner = getuser(token)
    user = params.get('user', default=None)
    appname = params.get('appname', default=None)
    ptype = params.get('type', default='invalid')

    if ptype not in VALID_TYPES:
        return reply(2, "Invalid running type: %s" % (ptype))
    if user is None or owner is None:
        return reply(1, "Unknown user")
    if appname is None:
        return reply(1, "Lack param: appname")
    if not checkvalid(owner, user, appname, ptype):
        return reply(1, "You don't have permission to this app!")

    pname = "%s...%s...%s...%s" % (ptype, owner, user, appname)
    runnerid = get_runnerid(pname)
    param = urllib.urlencode({'runnerid': runnerid})
    req = urllib2.urlopen(CONTROLLER+"/log", param)
    response = urllib2.urlopen(req)
    result = response.read()
    result = log_filter(result)
    return result


# interface for editor to get runner container status
@app.route("/runnerstat")
def runner_stat():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    token = params.get('token', default=None)
    owner = getuser(token)
    user = params.get('user', default=None)
    appname = params.get('appname', default=None)
    ptype = params.get('type', default='invalid')

    if ptype not in VALID_TYPES:
        return reply(2, "Invalid running type: %s" % (ptype))
    if user is None or owner is None:
        return reply(1, "Unknown user")
    if appname is None:
        return reply(1, "Lack param: appname")
    if not checkvalid(owner, user, appname, ptype):
        return reply(1, "You don't have permission to this runner!")
    pname = "%s...%s...%s...%s" % (ptype, owner, user, appname)
    runnerid = get_runnerid(pname)
    param = urllib.urlencode({'runnerid': runnerid})
    req = urllib2.urlopen(CONTROLLER+"/log",param)
    response = urllib2.urlopen(req)
    result = response.read()
    return result


# monitor status
@app.route("/")
def monitor():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    services = list()
    runners = list()
    stats = urllib2.urlopen(CONTROLLER+"/stats")
    for stat in stats:
            return None


if __name__ == "__main__":
   # Timer(TIME_INTERVAL, check).start()
    app.run(host="0.0.0.0",port=LOG_PORT, debug=True)