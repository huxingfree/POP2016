TOKEN="b8f7a273ad509ae2cab79e58e19aa392"
MANAGER="-H tcp://0.0.0.0:50000"
IMAGES="123.57.2.1:5000"

ALL=0

while getopts "a" arg
do
    case $arg in
	a)
            ALL=1
            ;;
    esac
done

if [ $ALL -eq 1 ]
then
    # stop controller.py
    kill -9 `ps aux | grep controller | awk '{print $2}'`
    
    # stop current docker
    docker rm -f `docker ps -a -q`

    unset DOCKER_TLS_VERIFY

    # start deamon
    nohup docker -H tcp://0.0.0.0:2385 -d --insecure-registry $IMAGES >/dev/null 2>&1 &

    sleep 5

    # join nodes
    nohup docker run -d swarm join --addr=123.57.2.1:2385 token://$TOKEN >/dev/null 2>&1
    nohup docker run -d swarm join --addr=123.57.145.224:2385 token://$TOKEN >/dev/null 2>&1
    nohup docker run -d swarm join --addr=182.92.236.173:2385 token://$TOKEN >/dev/null 2>&1

    sleep 5

    # start manager
    nohup docker run -d -p 50000:2375 swarm manage token://$TOKEN >/dev/null 2>&1

    sleep 5

    # remove all containers
    docker $MANAGER rm -f `docker $MANAGER ps -q`
else
    docker rm -f pop2016
    docker rm -f editor
fi

# start pop2016
rm -f /root/pop2016/docker.log
#if [ $WAR -eq 1 ]
#then
	unzip -o /root/pop2016/ROOT.war -d /root/pop2016/tomcat/webapps/ROOT/
	nohup docker run -id -p 80:8080 --name homepage -v /root/pop2016/tomcat/webapps/ROOT/:/usr/local/tomcat/webapps/ROOT/:ro pop2016/tomcat >/dev/null 2>&1
#else
#	nohup docker run -id -p 80:8080 --name pop2016 -v /root/pop2016/ROOT.war 
#fi
nohup docker logs -f -t homepage >/dev/null 2>/root/pop2016/docker.log &

# start editor
rm -f /root/editor/docker.log
unzip -o /root/editor/ROOT.war -d /root/editor/tomcat/webapps/ROOT/
nohup docker run -id -p 8000:8080 --name editor -v /root/editor/tomcat/webapps/ROOT/:/usr/local/tomcat/webapps/ROOT/:ro -v /root/data/:/data/:rw pop2016/tomcat >/dev/null 2>&1
nohup docker logs -t -f editor >/dev/null 2>/root/editor/docker.log &

# start registry
nohup docker run -d -p 5000:5000 --name registry -v /opt/data/registry:/tmp/registry registry >/dev/null 2>&1

# start javawebagent
nohup docker run -id -p 9001:8080 --name javawebagent -v /root/services/JavawebAgent/:/usr/local/tomcat/webapps/ROOT/:ro -v /root/data/:/data/:rw pop2016/tomcat >/dev/null 2>&1


if [ $ALL -eq 1 ]
then
    # start controller
    nohup python controller.py >/dev/null 2>/root/controller/controller.log &
fi

# output data
docker $MANAGER info
echo ""
docker $MANAGER images
echo ""
docker $MANAGER ps

echo ""
echo "Start succeed!"

