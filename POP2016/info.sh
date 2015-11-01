MANAGER="-H tcp://0.0.0.0:50000"
docker $MANAGER info
echo ""
docker $MANAGER images
echo ""
docker $MANAGER ps
