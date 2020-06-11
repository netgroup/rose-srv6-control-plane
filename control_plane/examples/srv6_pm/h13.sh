#source /root/venv/bin/activate

#source /home/user/Envs/srv6TutorialEnv/bin/activate

cd /home/rose/workspace/rose-srv6-data-plane/traffic-generator

PYTHON=python3

$PYTHON tg.py -6 -B fd00:0:13::2 -M 1000 -c fd00:0:83::2 -b 10M -t 3000 --measure-id 10 --generator-id 200 --verbose
