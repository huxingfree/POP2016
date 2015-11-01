from json import loads, dumps
from threading import Timer
from time import time
import MySQLdb

__author__ = 'user'

CONTROLLER = "http://123.57.2.1:60000/"
LOG_PORT = 70000
VALID_TYPES = ['php', 'python', 'javaweb'] # valid runner types
TIME_INTERVAL = 60
MANAGER = '-H tcp://0.0.0.0:50000'
# get user from token (according to database)
def getuser(token):
    if token is None:
        return None
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306)
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


def checkvalid(owner, user, appname, ptype):
    if owner is None or user is None or appname is None:
        return False
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin',
                               db='pop2016', port=3306)
    except Exception, e:
        return None
    cursor = conn.cursor()
    sql = "select app_name from app where app_type='%s' and owner_name='%s' and user_name='%s' and app_name='%s' limit 1" % (
    ptype, owner, user, appname)
    count = cursor.execute(sql)
    if count == 0:
        cursor.close()
        conn.close()
        return False
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return True


def obj_to_json(obj):
    return dumps(obj)


def reply(code, msg):
    return obj_to_json({'code': code, 'msg': msg})


def get_runnerid(pname):
    if pname is None:
        return None
    try:
        conn = MySQLdb.connect(host='rdsj7nhfyy0syt1fw980.mysql.rds.aliyuncs.com', user='useradmin', passwd='useradmin', db='pop2016', port=3306)
    except Exception,e:
        return None
    cursor = conn.cursor()
    sql = "select dockerid from log where pname='%s' limit 1" % (pname)
    count = cursor.execute(sql)
    if count ==0:
        cursor.close()
        conn.close()
        return None
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]


# filter the app log
def log_filter(text):
    return text
