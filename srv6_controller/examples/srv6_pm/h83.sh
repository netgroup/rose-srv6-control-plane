#source /root/venv/bin/activate

#source /home/user/Envs/srv6TutorialEnv/bin/activate

cd /home/rose/workspace/rose-srv6-data-plane/traffic-generator

PYTHON=python3

$PYTHON tg.py -s -B fd00:0:83::2 --measure-id 10 --generator-id 200 --verbose
