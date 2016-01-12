#!/usr/bin/env python
# -*- coding:utf-8 -*

from flask import Flask, request, render_template, Response
from time import localtime, time, strftime
from json import loads, dumps
import commands

__author__ = 'ckcz123'
__email__ = 'ckcz123@126.com'

MANAGER = '-H tcp://0.0.0.0:9950'
TOKEN = 'b8f7a273ad509ae2cab79e58e19aa392'
DOMAINS = ['123.57.2.1', '123.57.145.224', '182.92.236.173']
DOMAIN = '123.57.2.1' # domain of runners
PORT = 9999 # port on the controller
VALID_TYPES = ['php', 'python', 'javaweb'] # valid runner types

app = Flask(__name__)

def json_to_obj(json_str):
    try:
        obj = loads(json_str.replace("'", "\""))
    except Exception, e:
        return None
    else:
        return obj

def obj_to_json(obj):
    return dumps(obj)

def reply(code, msg):
    return obj_to_json({'code': code, 'msg': msg})

# get a valid port that is not used
def get_valid_port(start, end):
    global MANAGER
    for i in range(start, end):
        status, output = commands.getstatusoutput("docker %s ps | grep \":%d->\"" % (MANAGER, i))
        if status != 0:
            return i
    return -1

def run(ptype, path, node=None, port=None, memory=None, overload=False):
    global MANAGER
    constraint=''
    if node is not None:
        constraint=" -e constraint:node_name==node%d" % (int(node))
    if port is None:
        port=get_valid_port(1001, 1999)
    else:
        port=int(port)

    sshport=get_valid_port(4001, 6000)
    debugport=get_valid_port(3001, 4000)

    memlimit=''
    if memory is not None:
        memlimit=" -m %dM" % (int(memory))
    if overload:
        commands.getstatusoutput("docker %s rm -f `docker %s ps | grep ':%d->' | awk '{print $1}'`" % (MANAGER, MANAGER, port))

    if ptype=='php':
        code, output=commands.getstatusoutput("docker %s run -id%s -p %d:80 -p %d:22 -v /root/data/repo/php%s:/var/www/html/%s pop2016/php" % (MANAGER, memlimit, port, sshport, path, constraint))
    elif ptype=='python':
        code, output=commands.getstatusoutput("docker %s run -id%s -p %d:80 -p %d:22 -v /root/data/repo/python%s:/home/%s pop2016/python" % (MANAGER, memlimit, port, sshport, path, constraint))
    elif ptype=='javaweb':
        code, output=commands.getstatusoutput("docker %s run -id%s -p %d:8080 -p %d:22 -v /root/data/repo/javaweb/%s:/usr/local/tomcat/webapps/ROOT/%s pop2016/tomcat" % (MANAGER, memlimit, port, sshport, path, constraint))
    elif ptype=='javaweb-debug':
        code, output=commands.getstatusoutput("docker %s run -id%s -p %d:8080 -p %d:22 -p %d:9000 -v /root/data/repo/javaweb%s:/usr/local/tomcat/webapps/ROOT/%s pop2016/tomcat-debug" % (MANAGER, memlimit, port, sshport, debugport, path, constraint))
    else:
        return reply(2, "Invalid running type: %s" % (ptype))

    if code is 0:
        dockerid = output[0:12]
        code, output = commands.getstatusoutput("docker %s ps | grep %s" % (MANAGER, dockerid))
        for domain in DOMAINS:
            if domain in output:
                response = {'code': '0', 'domain': domain, 'port': "%d" % (port), 'sshport': "%d" % (sshport), 'dockerid': dockerid}
                if ptype=='javaweb-debug':
                    response['debugport']="%d" % (debugport)
                return obj_to_json(response)
        return reply(6, "Unable to find the domain")
    else:
        return reply(5, output)

def delete(dockerid):
    global MANAGER
    commands.getstatusoutput("docker %s rm -f %s" % (MANAGER, dockerid))
    return reply(0, 'Success')

def startservice(ptype, path=None, node=None, port=None, memory=None, overload=False):
    global MANAGER
    if node is None:
        node=1
    constraint=" -e constraint:node_name==node%d" % (int(node))
    if port is None:
        port=get_valid_port(2001, 2999)
    else:
        port=int(port)
    memlimit=''
    if memory is not None:
        memlimit=" -m %dM" % (int(memory))

    sshport=get_valid_port(4001, 6000)

    if overload:
        commands.getstatusoutput("docker %s rm -f `docker %s ps | grep ':%d->' | awk '{print $1}'`" % (MANAGER, MANAGER, port))

    if ptype=='tomcat':
        code, output=commands.getstatusoutput("docker %s run -id%s -p %d:8080 -p %d:22 -v /root/data/repo/:/data/repo/ -v /root/data/template/:/data/template/ -v /root/data/share/:/data/share/ -v /root/data/mvnrepo/repository/:/root/.m2/repository/ -v /root/data/service%s:/usr/local/tomcat/webapps/ROOT/%s pop2016/tomcat-server" % (MANAGER, memlimit, port, sshport, path, constraint))
    elif ptype=='gateone':
        code, output=commands.getstatusoutput("docker %s run -id%s -p %d:8000 -p %d:22%s pop2016/gateone" % (MANAGER, memlimit, port, sshport, constraint))
    else:
        code, output=commands.getstatusoutput("/bin/bash ../scripts/%s.sh" % (ptype))

    if code is 0:
        if ptype!='tomcat' and ptype!='gateone':
            return reply(0, "Success")
        dockerid = output[0:12]
        code, output = commands.getstatusoutput("docker %s ps | grep %s" % (MANAGER, dockerid))
        for domain in DOMAINS:
            if domain in output:
                response = {'code': '0', 'domain': domain, 'port': "%d" % (port), 'sshport': "%d" % (sshport), 'dockerid': dockerid}
                return obj_to_json(response)
        return reply(6, "Unable to find the domain")
    else:
        return reply(5, output)


def stat(dockerid=None):
    global MANAGER
    if dockerid is not None:
        status, output=commands.getstatusoutput("docker %s stats --no-stream %s" % (MANAGER, dockerid))
        if status==0:
            output=output.replace("/"," ").replace("\t"," ").replace("kB","KB").split("\n")
            st=output[1].split()
            return obj_to_json({"code":"0", "dockerid": st[0], "cpu": st[1], "memuse": st[2]+" "+st[3], "memall": st[4]+" "+st[5], "mempercent":st[6], "netin":st[7]+" "+st[8], "netout":st[9]+" "+st[10]})
        else:
            return reply(1, output)

    stats=[]

    status, output = commands.getstatusoutput("docker %s stats --no-stream `docker %s ps -q`" % (MANAGER, MANAGER))
    if status == 0:
        output = output.replace("/"," ").replace("\t"," ").replace("kB","KB")
        sts = output.split("\n")
        for i in range(1, len(sts)):
            st=sts[i].split()
            stat={"dockerid": st[0], "cpu": st[1], "memuse": st[2]+" "+st[3], "memall": st[4]+" "+st[5], "mempercent":st[6], "netin":st[7]+" "+st[8], "netout":st[9]+" "+st[10]}
            stats.append(stat)

    return obj_to_json(stats)

def servicestat(dockerid, ptype='tomcat'):
    if ptype=='tomcat':
        status, output=commands.getstatusoutput("docker %s exec -i %s ps aux | grep java -m 1 | awk '{print $8}'" % (MANAGER, dockerid))
        if status==0:
            return obj_to_json({"code":"0", "stat":output})
        else:
            return reply(1, output)

    if ptype=='registry':
        status, output=commands.getstatusoutput("docker %s exec -i registry ps aux | grep java -m 1 | awk '{print $8}'" % (MANAGER))
        if status==0:
            return obj_to_json({"code":"0", "stat":output})
        else:
            return reply(1, output)
    else:
        return reply(1, "unknown service")

def log(dockerid, ptype):
    global MANAGER
    if ptype=='php':
        status, output = commands.getstatusoutput("docker %s exec -i %s /bin/cat /var/www/error.log" % (MANAGER, dockerid))
    elif ptype=='python':
        status, output = commands.getstatusoutput("docker %s logs -t %s" % (MANAGER, dockerid))
    elif ptype=='tomcat':
        date=strftime("%Y-%m-%d", localtime(time()))
        status, output=commands.getstatusoutput("docker %s exec -i %s /bin/cat /usr/local/tomcat/logs/catalina.%s.log" % (MANAGER, dockerid, date))
    else:
        return reply(1, "Unknown type")

    if status==0:
        return obj_to_json({"code":0, "log":output})
    else:
        return reply(1, output)

def nodestat():
    global MANAGER
    code, output=commands.getstatusoutput("docker %s info" % (MANAGER))
    return obj_to_json({"code":0, "nodestat":output})

def ps():
    global MANAGER
    code, output=commands.getstatusoutput("docker %s ps" % (MANAGER))
    return "<pre>"+output+"</pre>"

@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form
    action=params.get('action', default=None)
    path=params.get('path', default=None)
    ptype=params.get('type', default=None)
    port=params.get('port', default=None)
    node=params.get('node', default=None)
    memory=params.get('memory', default=None)
    dockerid=params.get('dockerid', default=None)
    overload=params.get('overload', default=None)
    if overload is not None:
        overload=True
    else:
        overload=False

    if action=='run':
        return run(ptype, path, node, port, memory, overload)
    if action=='startservice':
        return startservice(ptype, path, node, port, memory, overload)
    if action=='stat':
        return stat(dockerid)
    if action=='delete':
        return delete(dockerid)
    if action=='servicestat':
        if ptype is None:
            ptype='tomcat'
        return servicestat(dockerid, ptype)
    if action=='log':
        return log(dockerid, ptype)
    if action=='nodestat':
        return nodestat()
    if action=='ps':
        return ps()

    return reply(0, "unknown request")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)


