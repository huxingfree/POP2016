import sys
from json import loads
from container_manager import startservice
import MySQLdb
from time import localtime, time, strftime
import logging
__author__ = 'user'

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
    logging.basicConfig(filename = LOG_FILE, level = logging.ERROR)

    type = 'tomcat'
    node = 1
    overload = True
    memory = None
    path = '/'+service_name+'/'
    if service_name == 'gateone':
        type = 'gateone'
        path = None

    res = startservice(type, path, node, port, memory, overload)
    res = loads(res)
    currtime = get_current_time()

    if int(res['code'])!=0:
        logging.error(currtime+" Fail: "+res['msg'])
        print "Fail:"+res['msg']
    else:
        conn = mysql_con()
        cursor = conn.cursor()
        sql = "SELECT id FROM home_service WHERE service_name = '%s'" % service_name
        count = cursor.execute(sql)
        if count==0:
            sql = "insert into home_service(service_name,service_type,create_time,domain,port) VALUES ('%s','%s','%s','%s','%d')" % (service_name,type,currtime,res['domain'],int(res['port']))
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception, e:
                pass
        result = cursor.fetchone()
        serviceid = result[0]
        sql = "SELECT dockerid FROM home_service_instance WHERE serviceid='%d'" % serviceid
        count = cursor.execute(sql)
        if count == 0:
            sql = "insert into home_service_instance(dockerid,domain,port,sshport,serviceid,node) VALUES ('%s','%s', %d, %d, %d, %d)" %(res['dockerid'],res['domain'],int(res['port']),int(res['sshport']),serviceid,node)
            try:
                cursor.execute(sql)
                conn.commit()
                print currtime+" "+service_name + " starts success"
            except Exception,e:
                pass

        else:
            sql = "update home_service_instance SET dockerid='%s', sshport=%d WHERE serviceid=%d " % (res['dockerid'], res['sshport'], serviceid)
            try:
                cursor.execute(sql)
                conn.commit()
                print currtime+" "+service_name + " starts success"
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


if len(sys.argv) == 1:
    init_all()
else:
    start(sys.argv[1], sys.argv[2])



