#source /root/venv/bin/activate
#export PYTHONPATH=/opt/lmg/grpc-services/protos/gen-py
cd /home/rose/workspace/rose-srv6-control-plane

PYTHON=python3

cd ./srv6_controller/examples/srv6_pm

sudo $PYTHON srv6_pm_example.py
