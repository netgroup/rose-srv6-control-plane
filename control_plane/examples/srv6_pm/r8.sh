#source /root/venv/bin/activate
#export PYTHONPATH=/root/lmg/grpc-services/protos/gen-py:/opt/xdp_experiments/srv6-pfplm
#export PYTHONPATH=/home/user/repos/xdp_experiments/srv6-pfplm

PYTHON=python3

cd /home/rose/workspace/rose-srv6-control-plane

cd ./srv6_controller/node-manager

$PYTHON node_manager.py
