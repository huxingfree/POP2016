from flask import *
from container_manager import *
from json import loads, dumps
import string
import MySQLdb
from time import localtime, time, strftime
from threading import Timer
import smtplib
from email.mime.text import MIMEText
__author__ = 'Hu Xing'

LOG_PORT = 9222
VALID_TYPES = ['php', 'python', 'javaweb'] # valid runner types
TIME_INTERVAL = 600


# format current time as a string
def get_current_time(timestamp=None):
    if timestamp is None:
        timestamp=time();
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))


# connect to mysql
def mysql_con():
    try:
       conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                              db='pop2016', port=3306)
    except Exception, e:
        return None
    return conn


def obj_to_json(obj):
    return dumps(obj)


def reply(code, msg):
    return obj_to_json({'code': code, 'msg': msg})


app = Flask(__name__)


@app.route("/",methods=['GET','POST'])
def index():
    if session.get('username')=='admin' and session.get('password')=='admin':
        return redirect(url_for('monitor'))
    else:
        return render_template("index.html")


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form['username']=="admin" and request.form['password']=="admin":
            session['username']=request.form['username']
            session['password']=request.form['password']
            return redirect(url_for('monitor'))
        else:
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('password',None)
    return redirect(url_for('index'))


# interface for editor to get app log
@app.route("/applog", methods=['GET','POST'])
def app_log():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    dockerid = params.get('dockerid',default=None)
    ptype = params.get('type', default='invalid')
    result = log(dockerid, ptype)
    return result
"""
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
  #  runnerid = get_runnerid(pname)
  """

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
    dockerid = params.get('dockerid',default=None)
    result = stat(dockerid)
    return result
    """
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
   # runnerid = get_runnerid(pname)
   """

    # param = urllib.urlencode({'runnerid': runnerid})
    # req = urllib2.urlopen(CONTROLLER+"/log",param)
    # response = urllib2.urlopen(req)
    # result = response.read()


def send_mail(report):
    SENDER = '2269077178@qq.com'
    RECEIVIER = 'huxing0101@pku.edu.cn'
    SUBJECT = 'POP2016 minotor'
    SMTPSERVER = 'smtp.qq.com'
    USERNAME = '2269077178@qq.com'
    PASSWORD = 'XINfang199311'
    str = '<html><h1>Warning!</h1></html>'+'<table border="1"><tr><th>Docker ID</th><th>CPU</th><th>mempercent</th></tr>'
    for st in report:
        str = str + '<tr><td>'+st['dockerid']+'</td><td>'+st['cpu']+'</td><td>'+st['mempercent']+'</td></tr>'
    str = str+'</table>'
    msg = MIMEText(str,'html','utf-8')
    msg['Subject'] = SUBJECT
    smtp = smtplib.SMTP()
    smtp.connect(SMTPSERVER)
    smtp.login(USERNAME,PASSWORD)
    smtp.sendmail(SENDER,RECEIVIER,msg.as_string())
    smtp.quit()


# get all docker stats every 1 min
def check_docker_stats():
    global TIME_INTERVAL
    conn = mysql_con()
    cursor = conn.cursor()

    currtime = get_current_time()
    stats = stat()
    stats= loads(stats)
    report = []
    for st in stats:
        cpu = round(float(st['cpu'][0:-1]),2)
        memuse = st['memuse'].split(' ')
        # memuse unit is 'MB'
        if memuse[1]=='B':
            memuse = round(float(memuse[0])/(1024*1024), 2)
        elif memuse[1]=='KB':
            memuse = round(float(memuse[0])/1024, 2)
        elif memuse[1]=='GB':
            memuse = round(float(memuse[0])*1024, 2)
        elif memuse[1]=='MB':
            memuse = round(float(memuse[0]),2)
        memall = st['memall'].split(' ')
        if memall[1]=='GB':
            memall = round(float(memall[0])*1024, 2)
        elif memall[1]=='KB':
            memall = round(float(memall[0])/1024,2)
        elif memall[1]=='B' :
            memall = round(float(memall[0])/(1024*1024),2)
        elif memall[1]=='MB':
            memall = round(float(memall[0]),2)
        mempercent = round(float(st['mempercent'][0:-1]),2)

        # net unit is 'KB
        netin = st['netin'].split(' ')
        if netin[1]=='B':
            netin = round(float(netin[0])/1024,2)
        elif netin[1]=='MB':
            netin = round(float(netin[0])*1024,2)
        elif netin[1]=='KB':
            netin = round(float(netin[0]),2)
        netout = st['netout'].split(' ')
        if netout[1]=='B':
            netout = round(float(netout[0])/1024,2)
        elif netout[1]=='MB':
            netout = round(float(netout[0])*1024,2)
        elif netout[1]=='KB':
            netout = round(float(netout[0]),2)
        sql = "insert into dockerstat(dockerid,time,cpu,memuse,memall,mempercent,netin,netout) VALUES ('%s', '%s', %f, %f, %f, %f, %f, %f)" % (st['dockerid'], currtime, cpu , memuse, memall, mempercent, netin, netout)
        try:
            cursor.execute(sql)
            conn.commit()
        except Exception, e:
            pass
        if mempercent>80:
            report.append(st)
    cursor.close()
    conn.close()
    if len(report) > 0:
        send_mail(report)
    Timer(TIME_INTERVAL, check_docker_stats).start()


def get_info(dockerid):
    conn = mysql_con()
    mems = []
    cpus = []
    netins = []
    netouts = []
    sql = "select time, cpu, memuse , memall, netin, netout FROM dockerstat WHERE dockerid = '%s'" % dockerid
    cursor = conn.cursor()
    count = cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        cpu = dict(time=result[0], cpu = result[1])
        memusg = dict(time=result[0],mem = result[2])
        netin = dict(time = result[0],netin = result[4])
        netout = dict(time = result[0],netout = result[5])

        cpus.append(cpu)
        mems.append(memusg)
        netins.append(netin)
        netouts.append(netout)
    cursor.close()
    conn.close()
    infor = dict(cpus = cpus, mems = mems, netins = netins, netouts = netouts)
    return infor


@app.route('/dockerstat',methods=['GET','POST'])
def dockerstst():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    dockerid = params.get('dockerid')
    infor = get_info(dockerid)
    cpus = infor['cpus']
    mems = infor['mems']
    netins = infor['netins']
    netouts = infor['netouts']
    return render_template('dockerstat.html', mems=mems, cpus=cpus, netins=netins, netouts=netouts)


# home services are displayed default
@app.route("/monitor")
def monitor():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    home_service = []
    runners = []
    services = []
    conn = mysql_con()
    cursor = conn.cursor()

    sql = "select dockerid, service_name, domain, port, sshport FROM home_service"
    count = cursor.execute(sql)
    currtime = get_current_time()
    if count>0:
        results = cursor.fetchall()
        for result in results:
            s=dict(name=result[1], domain=result[2], port=result[3], sshport=result[4])
            res = stat(result[0])
            res = loads(res)
            if int(res['code']) != 0:
                continue
            else:
                s = dict(s.items()+res.items())
                home_service.append(s)
                continue

    sql = "SELECT id, service_name,service_type,owner_name,plugin_address,create_date FROM service"
    count = cursor.execute(sql)
    if count>0:
        results = cursor.fetchall()
        for result in results:
            service_intance = []
            sq = "SELECT dockerid,domain, port,sshport FROM service_instance WHERE service_id='%s'" % result[0]
            ct = cursor.execute(sq)
            if ct > 0:
                rts = cursor.fetchall()
                for rt in rts:
                    s = dict(domain=rt[1], port=rt[2], sshport=rt[3])
                    res = stat(rt[0])
                    res = loads(res)
                    if int(res['code']) != 0:
                        continue
                    else:
                        s = dict(s.items()+res.items())
                        service_intance.append(s)
                        continue
            ss = dict(serviceid=result[0], name=result[1], type=result[2], owner=result[3], instances=service_intance, address=result[4], create_time=result[5])
            services.append(ss)


    sql = "SELECT dockerid, app_name, app_type, user_name, owner_name, app_instance.domain, port,sshport FROM app_instance, app WHERE app_instance.appid=app.id"
    count = cursor.execute(sql)
    currtime = get_current_time()
    if count>0:
        results = cursor.fetchall()
        for result in results:
            s = dict(name=result[1], type=result[2], user=result[3], owner=result[4], domain=result[5], port=result[6], sshport=result[7])
            res = stat(result[0])
            res = loads(res)
            if int(res['code']) != 0:
                continue
            else:
                s = dict(s.items()+res.items())
                runners.append(s)
                continue
    return render_template('monitor.html', runners=runners, services=services, home_service=home_service, currtime=currtime)

"""
@app.route("/monitor")
def monitor():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    # all docker stats
    stats = stat()
    stats = loads(stats)
    currtime = get_current_time()
    conn = mysql_con()
    cursor = conn.cursor()
    home_service = []
    runners = []
    services = []
    service_instance = []
    for st in stats:
        dockerid = st['dockerid']
        # select home services
        sql = "SELECT service_name, domain, port,sshport FROM home_service WHERE dockerid = '%s' limit 1" % dockerid
        count = cursor.execute(sql)
        if count == 1:
            result = cursor.fetchone()
            s = dict(name=result[0], domain=result[1], port=result[2], sshport=result[3])
            s = dict(s.items()+st.items())
            home_service.append(s)
            continue
        # select runners
        sql = "SELECT app_name, app_type, user_name, owner_name, domain, port,sshport FROM app_instance, app WHERE dockerid='%s' AND app_instance.appid=app.id limit 1" % dockerid
        count = cursor.execute(sql)
        if count == 1:
            result = cursor.fetchone()
            s = dict(name=result[0], type=result[1], user=result[2], owner=result[3], domain=result[4], port=result[5], sshport=result[6])
            s = dict(s.items()+st.items())
            runners.append(s)
            continue
        # select services
        sql = "SELECT service_name, service_type, owner_name, domain, port,sshport FROM service, service_instance WHERE dockerid='%s' AND service.id=service_instance.service_id limit 1" % dockerid
        count = cursor.execute(sql)
        if count == 1:
            result = cursor.fetchone()
            s = dict(name=result[0], type=result[1], owner=result[2], domain=result[3], port=result[4], sshport=result[5])
            s = dict(s.items()+st.items())
            services.append(s)
            continue
    return render_template('monitor.html', runners=runners, services=services, home_service=home_service, currtime=currtime)
"""
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
    Timer(TIME_INTERVAL, check_docker_stats).start()
    app.run(host="0.0.0.0", port=LOG_PORT, debug=True, use_reloader=False)
