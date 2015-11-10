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
    service_stats = {}
    stats = urllib2.urlopen(CONTROLLER+"/stats")
    runners_stats={}
    runners = []
    services = []
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306)
    except Exception, e:
        return None
    cursor = conn.cursor()
    for stat in stats:
        dockerid = stat['dockerid']
        sql = "select sname,url from home_service where dockerid='%s' limit 1" % (dockerid)
        count = cursor.execute(sql)
        if count ==0:
            runners_stats[stat['dockerid']] = stat
        else:
            result = cursor.fetchone()
            service_name = result[0]
            url = result[1]
            service_stats[service_name] = stat
            service = dict(url = url,service_name = service_name )
            services.append(dict(service.items()+stat.items()))
    for item in all_runners.items():
        runner = item[1]
        runners.append(dict(runner.items()+runners_stats[runner['dockerid']].items()))



if __name__ == "__main__":
   # Timer(TIME_INTERVAL, check).start()
    app.run(host="0.0.0.0",port=LOG_PORT, debug=True)