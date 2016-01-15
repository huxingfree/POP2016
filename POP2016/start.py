import sys
from json import loads
from container_manager import startservice
import MySQLdb
from time import localtime, time, strftime
import logging

__author__ = 'Hu Xing'

LOG_FILE = "./start.log"


# connect to mysql
def mysql_con():
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306)
    except Exception, e:
        return None
    return conn


# format current time as a string
def get_current_time(timestamp=None):
    if timestamp is None:
        timestamp = time()
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))


# start home services
def start(service_name, port):
    logging.basicConfig(filename=LOG_FILE, level=logging.ERROR)
    conn = mysql_con()
    cursor = conn.cursor()

    currtime = get_current_time()
    type = 'tomcat'
    node = 1
    overload = True
    memory = None
    path = '/' + service_name + '/'
    if service_name == 'gateone':
        type = 'gateone'
        path = None
    res = startservice(type, path, node, port, memory, overload)
    res = loads(res)

    if int(res['code']) != 0:
        logging.error(currtime + " Fail: " + res['msg'])
        print "Fail:" + res['msg']

    sql = "SELECT service_id FROM home_service WHERE service_name = '%s'" % service_name
    count = cursor.execute(sql)
    result = cursor.fetchone()
    sql = "DELETE FROM home_service_instance WHERE port =%d" % int(res['port'])
    count = cursor.execute(sql)
    sql = "INSERT INTO home_service_instance(dockerid,domain,service_id,port,sshport,node,create_time) VALUES ('%s',%d,'%s',%d,%d,%d,'%s')" % (res['dockerid'],result[0],res['domain'],int(res['port']), node, int(res['sshport']))
    try:
        cursor.execute(sql)
        conn.commit()
        print currtime + " " + service_name + " starts success"
    except Exception, e:
        pass
    cursor.close()
    conn.close()


def init_all():
    start('homepage', 80)
    start('editor', 8000)
    start('javaweb-compiler', 3000)
    start('gateone', 4000)
    start('pop2016-completion', 9300)
    start('findbugs', 9400)


if len(sys.argv) == 1:
    init_all()
else:
    start(sys.argv[1], sys.argv[2])
