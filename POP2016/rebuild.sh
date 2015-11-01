TOKEN="b8f7a273ad509ae2cab79e58e19aa392"
MANAGER="-H tcp://0.0.0.0:50000"
IMAGES="123.57.2.1:5000"

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

nohup docker run -d -p 5000:5000 --name registry -v /opt/data/registry:/tmp/registry registry >/dev/null 2>&1
 
# remove all containers
docker $MANAGER rm -f `docker $MANAGER ps -q`

ONLY=0
TOMCAT=0
PHP=0
PYTHON=0
while getopts "abco" arg
do
    case $arg in
	a)
	    TOMCAT=1;;
	b)
	    PHP=1;;
	c)
	    PYTHON=1;;
        o)
            ONLY=1;;
    esac
done

if [ $TOMCAT -eq 1 ];
then
	if [ $ONLY -eq 0 ];
	then
		docker rmi -f pop2016/tomcat
		docker build -t pop2016/tomcat /root/build/tomcat/
		docker tag -f pop2016/tomcat $IMAGES/tomcat
		docker push $IMAGES/tomcat
		docker $MANAGER rmi -f pop2016/tomcat
	fi
	docker $MANAGER pull $IMAGES/tomcat
	docker $MANAGER tag -f $IMAGES/tomcat pop2016/tomcat
fi

if [ $PHP -eq 1 ];
then
	if [ $ONLY -eq 0 ];
	then
		docker rmi -f pop2016/php
		docker build -t pop2016/php /root/build/php/
		docker tag -f pop2016/php $IMAGES/php
		docker push $IMAGES/php
		docker $MANAGER rmi -f pop2016/php
	fi
	docker $MANAGER pull $IMAGES/php
	docker $MANAGER tag -f $IMAGES/php pop2016/php
fi

if [ $PYTHON -eq 1 ];
then
	if [ $ONLY -eq 0 ];
	then
		docker rmi -f pop2016/python
		docker build -t pop2016/python /root/build/python/
		docker tag -f pop2016/python $IMAGES/python
		docker push $IMAGES/python
		docker $MANAGER rmi -f pop2016/python
	fi
	docker $MANAGER pull $IMAGES/python
	docker $MANAGER tag -f $IMAGES/python pop2016/python
fi

sleep 3

# output images
docker $MANAGER info
echo ""
docker $MANAGER images
echo ""
curl http://$IMAGES/v1/search
echo ""

echo "Rebuild succeed!"
echo "Please run 'bash start.sh -a' to start the service"
