#from threading import Timer
from flask import *
from container_manager import *
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
    result = log(runnerid, ptype)
    return result
    # param = urllib.urlencode({'runnerid': runnerid,'type':ptype})
    # req = urllib2.urlopen(CONTROLLER+"/log", param)
    # response = urllib2.urlopen(req)
    # result = response.read()
    # result = log_filter(result)


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
    result = stat(runnerid)
    # param = urllib.urlencode({'runnerid': runnerid})
    # req = urllib2.urlopen(CONTROLLER+"/log",param)
    # response = urllib2.urlopen(req)
    # result = response.read()
    return result


@app.route("/")
def monitor():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    # stats = urllib2.urlopen(CONTROLLER+"/stat")
    stats = stat()  # all docker containers' stats
    service_stats = {}  # home_services' stats
    runners_stats = {}  # runners' stats
    runners = []  # runners list
    services = []  # home_services list
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306)
    except Exception, e:
        return None
    cursor = conn.cursor()
    for pstat in stats:
        dockerid = pstat['dockerid']
        sql = "select hsname,url from home_services where dockerid='%s' limit 1" % (dockerid)
        count = cursor.execute(sql)
        if count == 0:
            runners_stats[dockerid] = stat
        else:
            result = cursor.fetchone()
            service_name = result[0]
            url = result[1]
            service_stats[service_name] = stat
            if service_name == 'gateone'or service_name == 'registry':
                service_stat = servicestat(dockerid, service_name)
            else:
                service_stat = servicestat(dockerid)
            service = dict(url=url, service_name=service_name, service_stat=service_stat)
            services.append(dict(service.items()+stat.items()))
    for item in all_runners.items():
        runner = item[1]
        runners.append(dict(runner.items()+runners_stats[runner['dockerid']].items()))



if __name__ == "__main__":
   # Timer(TIME_INTERVAL, check).start()
    app.run(host="0.0.0.0",port=LOG_PORT, debug=True)