#!/usr/bin/env python
# -*- coding:utf-8 -*

from flask import Flask, request, render_template, Response
from time import localtime, time, strftime
from json import loads, dumps
from threading import Timer
import commands
import MySQLdb

__author__ = 'ckcz123'
__email__ = 'ckcz123@126.com'

MANAGER = '-H tcp://0.0.0.0:50000'
TOKEN = 'b8f7a273ad509ae2cab79e58e19aa392'
DOMAINS = ['123.57.2.1', '123.57.145.224', '182.92.236.173']

DOMAIN = '123.57.2.1' # domain of runners
PORT = 60000 # port on the controller
VALID_TYPES = ['php', 'python', 'javaweb'] # valid runner types
LIMIT = 600
TIME_INTERVAL = 60

all_runners = {}
app = Flask(__name__)


# format current time as a string
def format_time(timestamp=None):
    if timestamp is None:
        timestamp=time();
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))


def json_to_obj(json_str):
    try:
        obj = loads(json_str.replace("'", "\""))
    except Exception, e:
        return None
    else:
        return obj


def obj_to_json(obj):
    return dumps(obj)


def mysql_log(runner, op):
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin', db='pop2016', port=3306)
    except Exception, e:
        return None
    cursor = conn.cursor()
    sql = "insert into log (pname, action, domain, port, dockerid, ptype, appname, owner, user, deploy_time, action_time) values ('%s', '%s', '%s', %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (runner['pname'], op, runner['domain'], runner['port'], runner['dockerid'], runner['ptype'], runner['appname'], runner['owner'], runner['user'], runner['time'], format_time())
    try:
        cursor.execute(sql)
        conn.commit()
    except Exception, e:
        pass
    cursor.close()
    conn.close()

def checkvalid(owner, user, appname, ptype):
    if owner is None or user is None or appname is None:
        return False
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin', db='pop2016', port=3306)
    except Exception, e:
        return None
    cursor = conn.cursor()
    sql = "select app_name from app where app_type='%s' and owner_name='%s' and user_name='%s' and app_name='%s' limit 1" % (ptype, owner, user, appname)
    count = cursor.execute(sql)
    if count == 0:
        cursor.close()
        conn.close()
        return False
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return True

def reply(code, msg):
    return obj_to_json({'code': code, 'msg': msg});

# get user from token (according to database)
def getuser(token):
    if token is None:
        return None
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin', db='pop2016', port=3306)
    except Exception, e:
        return None
    cursor = conn.cursor()
    sql = "select username from user where token='%s' limit 1" % (token)
    count = cursor.execute(sql)
    if count == 0:
        cursor.close()
        conn.close()
        return None
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]

def reply(code, msg):
    return obj_to_json({'code': code, 'msg': msg});

def get_runner(pname):
    return all_runners.get(pname, None)

# check every 5 minutes
def check():
    global all_runners
    global LIMIT
    global TIME_INTERVAL
    global MANAGER
    currtime = time()
    dockers = []
    runners = [item[1] for item in all_runners.items()]
    overs = []
    # get all runner pname that is overtime
    for runner in runners:
        timestamp = runner['timestamp']
        if currtime - timestamp > LIMIT:
            overs.append(runner['pname'])
    # delete them
    for over in overs:
        if over in all_runners:
            mysql_log(get_runner(over), 'auto-remove')
            del all_runners[over]
    # get all docker id that is running    
    status, output = commands.getstatusoutput("docker %s ps | grep \"\\.\\.\\.\" | awk '{print $1}'" % (MANAGER))
    runnings = output.split("\n")
    # get all docker id that is in all_runners
    dockers = []
    runners = [item[1] for item in all_runners.items()]
    for runner in runners:
        dockerid = runner['dockerid']
        # if a runner in all_runners does not really exist
        if dockerid not in runnings:
            mysql_log(runner, 'auto-remove')
            del all_runners[runner['pname']]
        else:
            dockers.append(dockerid)
    # remove all containers that is not in all_runners
    for dockerid in runnings:
        if dockerid not in dockers:
            s, o = commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, dockerid))
    Timer(TIME_INTERVAL, check).start()


# get a valid port that is not used
def get_valid_port():
    for i in range(10001, 30000):
        status, output = commands.getstatusoutput("docker %s ps | grep \":%d->\"" % (MANAGER, i))
        if status != 0:
            return i
    return -1


def testrun():
    global MANAGER
    token = "ac9e1ae9df08a4193f1e5d3a656f41c2"
    owner = getuser(token)
    user = "ckcz123"
    appname = "test3"
    ptype = "php"
    print "token = %s ; owner = %s ; user = %s ; appname = %s ; ptype = %s" % (token, owner, user, appname, ptype)
    if ptype not in VALID_TYPES:
        return reply(2, "Invalid running type: %s" % (ptype))
    if user is None or owner is None:
        return reply(1, "Unknown user")
    if appname is None:
        return reply(1, "Lack param: appname")
    if not checkvalid(owner, user, appname, ptype):
        return reply(1, "You don't have permission to this app!")

    pname = "%s...%s...%s...%s" % (ptype, owner, user, appname)
    timestamp = time()
    runner = get_runner(pname)

    print pname

    # if runner exists: remove it.
    if runner is not None:
        commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, pname))    
        del all_runners[pname]

    # make a new runner
    port = get_valid_port()
    if port is -1:
        return reply(3, "Could not find a valid port.")

    print port

    code, output=commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, pname))
    print output
    if ptype == 'php':
        code, output = commands.getstatusoutput("docker %s run -id -p %d:80 -v /root/data/repo/php/%s/%s/:/var/www/html/ --name %s pop2016/php" % (MANAGER, port, owner, appname, pname))
    elif ptype == 'python':
        code, output = commands.getstatusoutput("docker %s run -id -p %d:80 -v /root/data/repo/python/%s/%s/:/home/ --name %s pop2016/python bash /root/start.sh" % (MANAGER, port, owner, appname, pname))

    print output

    if code is 0:
        dockerid = output[0:12];
        code, output = commands.getstatusoutput("docker %s ps | grep %s" % (MANAGER, dockerid))
        for domain in DOMAINS:
            if domain in output:
                runner = dict(pname=pname, dockerid=dockerid, domain=domain, port=port, ptype=ptype, owner=owner, user=user, appname=appname, timestamp=timestamp, time=format_time(timestamp))
                all_runners[pname] = runner
                mysql_log(runner, 'run')
                response = {'code': '0', 'path': "http://%s:%d/" % (runner['domain'], runner['port'])}
                return obj_to_json(response)
        return reply(6, "Unable to find the domain")
    else:
        return reply(5, output);


# start a runner
# if runner exists, just return it
@app.route("/run", methods=['GET', 'POST'])
def run():
    global MANAGER
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    token = params.get('token', default=None)
    owner = getuser(token)
    user = params.get('user', default=None)
    appname = params.get('appname', default=None)
    ptype = params.get('type', default='invalid')
    memlimit = params.get('memlimit', default='2048')
    if ptype not in VALID_TYPES:
        return reply(2, "Invalid running type: %s" % (ptype))
    if user is None or owner is None:
        return reply(1, "Unknown user")
    if appname is None:
        return reply(1, "Lack param: appname")
    if not checkvalid(owner, user, appname, ptype):
        return reply(1, "You don't have permission to this app!")

    pname = "%s...%s...%s...%s" % (ptype, owner, user, appname)
    timestamp = time()
    runner = get_runner(pname)

    # if runner exists: remove it.
    if runner is not None:
        commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, pname))    
        del all_runners[pname]

    # make a new runner
    port = get_valid_port()
    if port is -1:
        return reply(3, "Could not find a valid port.")

    commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, pname))
    if ptype == 'php':
        code, output = commands.getstatusoutput("docker %s run -id -m %sM -p %d:80 -v /root/data/repo/php/%s/%s/:/var/www/html/ --name %s pop2016/php" % (MANAGER, memlimit, port, owner, appname, pname))
    elif ptype == 'python':
        code, output = commands.getstatusoutput("docker %s run -id -m %sM -p %d:80 -v /root/data/repo/python/%s/%s/:/home/ --name %s pop2016/python bash /root/start.sh" % (MANAGER, memlimit, port, owner, appname, pname))
    elif ptype == 'javaweb':
        code, output = commands.getstatusoutput("docker %s run -id -p %d:8080 -v /root/data/repo/javaweb/%s/%s/target/%s/:/usr/local/tomcat/webapps/ROOT/ --name %s pop2016/tomcat" % (MANAGER, port, owner, appname, appname, pname))

    if code is 0:
        dockerid = output[0:12];
        code, output = commands.getstatusoutput("docker %s ps | grep %s" % (MANAGER, dockerid))
        for domain in DOMAINS:
            if domain in output:
                runner = dict(pname=pname, dockerid=dockerid, domain=domain, port=port, ptype=ptype, owner=owner, user=user, appname=appname, timestamp=timestamp, time=format_time(timestamp))
                all_runners[pname] = runner
                mysql_log(runner, 'run')
                response = {'code': '0', 'path': "http://%s:%d/" % (runner['domain'], runner['port'])}
                return obj_to_json(response)
        return reply(6, "Unable to find the domain")
    else:
        return reply(5, output);
    

@app.route("/delete", methods=['POST'])
def delete():
    global MANAGER
    params = request.form
    pname = params.get('pname', default=None)
    if pname is not None:
        commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, pname))    
        if pname in all_runners:
            mysql_log(get_runner(pname), 'remove')
            del all_runners[pname]
    return reply(0, 'Success')

# check log
# log file in php runner: /var/www/error.log
@app.route("/log", methods=['GET', 'POST'])
def log():
    global MANAGER
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
    timestamp = time()
    runner = get_runner(pname)
    if runner is None:
        return reply(3, "Runner does not exist. Please run it again.")
    
    dockerid = runner['dockerid']
    status, output=commands.getstatusoutput("docker %s ps | grep %s" % (MANAGER, dockerid))
    if status is not 0:
        return reply(3, "Runner does not exist. Please run it again.")

    ptype = runner['ptype']
    if ptype == 'php':
        status, output = commands.getstatusoutput("docker %s exec -i %s /bin/cat /var/www/error.log" % (MANAGER, dockerid))
    elif ptype == 'python':
        status, output = commands.getstatusoutput("docker %s logs -t %s" % (MANAGER, dockerid))

    if output == "":
        output = "There is no error in your project."
    resp = Response(output)
    resp.headers['Content-type'] = 'text/plain; charset=utf-8'
    return resp 

# monitor status
@app.route("/", methods=['GET'])
def monitor():
    # check if homepage exists
    homepage = dict(id = 'homepage', status = False)
    status, output = commands.getstatusoutput("docker ps | grep homepage | awk '{print $1}'")
    if status == 0:
        homepage['status'] = True
        homepage['dockerid'] = output
        homepage['path'] = "http://%s/" % (DOMAIN)
        status, output = commands.getstatusoutput("docker exec -i homepage ps aux | grep java -m 1 | awk '{print $8}'")
        if status == 0:
            homepage['status'] = output
        

    services = list()
    # check if some servces exists

    # check if editor exists
    status, output = commands.getstatusoutput("docker ps | grep editor | awk '{print $1}'")
    if status == 0 and output != "":
        editor = dict(id = 'editor', path = "http://%s:8000/" % (DOMAIN), dockerid = output)
        status, output = commands.getstatusoutput("docker exec -i editor ps aux | grep java -m 1 | awk '{print $8}'")
        if status == 0:
            editor['status'] = output
        services.append(editor)

    # registry
    status, output = commands.getstatusoutput("docker ps | grep registry | awk '{print $1}'")
    if status == 0 and output != "":
        registry = dict(id = 'registry', path = "http://%s:5000/" % (DOMAIN), dockerid = output)
        status, output = commands.getstatusoutput("docker exec -i registry ps aux | grep root -m 1 | awk '{print $8}'")
        if status == 0:
            registry['status'] = output
        services.append(registry)

    # javawebagent
    status, output = commands.getstatusoutput("docker ps | grep javawebagent | awk '{print $1}'")
    if status == 0 and output != "":
        javawebagent = dict(id = 'javawebagent', path = "http://%s:9001/" % (DOMAIN), dockerid = output)
        status, output = commands.getstatusoutput("docker exec -i javawebagent ps aux | grep java -m 1 | awk '{print $8}'")
        if status == 0:
            javawebagent['status'] = output
        services.append(javawebagent)
    

    stats = {}
    status, output = commands.getstatusoutput("docker %s stats --no-stream `docker %s ps -q`" % (MANAGER, MANAGER))
    if status == 0:
        output = output.replace("/"," ").replace("\t"," ").replace("kB","KB")
        sts = output.split("\n")
        for i in range(1, len(sts)):
            st = sts[i].split()
            stat = dict(dockerid=st[0], cpu=st[1], memuse=st[2]+" "+st[3], memall=st[4]+" "+st[5], mempercent=st[6], netin=st[7]+" "+st[8], netout=st[9]+" "+st[10])
            stats[st[0]]=stat

    runners=[]
    for item in all_runners.items():
        runner = item[1]
        runners.append(dict(runner.items()+stats[runner['dockerid']].items()))

    return render_template('monitor.html', runners=runners, length=len(all_runners), services=services, homepage=homepage)

if __name__ == "__main__":
    Timer(TIME_INTERVAL, check).start()
    #app.run(host="0.0.0.0", port=PORT)
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)


