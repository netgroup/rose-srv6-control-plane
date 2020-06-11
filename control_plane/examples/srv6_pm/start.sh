#!/bin/bash

#TOPO_PATH=/opt/rose-srv6-tutorial/nets/8r-1c-srv6-pm
#M_PATH=/opt/lmg/scripts
#SCRIPTS_PATH=/opt/lmg/scripts

TOPO_PATH=/home/rose/workspace/rose-srv6-tutorial/nets/8r-1c-srv6-pm
M_PATH=.
SCRIPTS_PATH=.
PYTHON=python3

echo "Starting tmux..."

tmux new-session -d -s mn

tmux set -g pane-border-status bottom
#tmux set-option -g mouse on

tmux new-window -a -t mn -n mn-cli "bash"
tmux send-keys -t mn-cli "cd $TOPO_PATH; sudo $PYTHON isis8d.py" C-m

mn_hosts=( r1 r2 r3 r4 r5 r6 r7 r8 h11 h12 h13 h31 h32 h33 h51 h52 h53 h81 h82 h83 hdc1 hdc2 hdc3 )

for host in "${mn_hosts[@]}"
do
    tmux new-window -a -t mn -n mn-"${host}" "bash"
    tmux send-keys -t mn-"${host}" "cd $M_PATH; sudo bash m ${host}; ret=$?; while true; do if [ $ret == 0 ]; then break; fi; printf '${host} not ready\n'; sleep 1; sudo bash m ${host}; ret=$?; done; printf '\n\n*** Logged to ${host} shell\n\n'" C-m
    tmux select-pane -t 0 -T mn-"${host}"
done

tmux new-window -a -t mn -n mn-controller
tmux select-pane -t 0 -T mn-controller

#tmux new-window -a -t mn -n mn-cli
tmux select-window -t mn-cli
tmux select-pane -t 0 -T mn-cli

tmux select-pane -t 0
tmux join-pane -v -s mn:mn-h13
tmux join-pane -h -s mn:mn-h83
tmux select-pane -t 0
tmux join-pane -v -s mn:mn-r1
tmux join-pane -h -s mn:mn-r8
tmux select-pane -t 0
tmux join-pane -v -s mn:mn-controller

# Select mn-cli pane
tmux select-pane -t 0

# Wait for Mininet topology
#sleep 10

# Start sender on r1
tmux send-keys -t 2 "printf '\n*** Starting node manager...\n'; sleep 20; printf '*** Started\n\n'; cd $SCRIPTS_PATH; bash r1.sh" C-m

# Start reflector on r8
tmux send-keys -t 3 "printf '\n*** Starting node manager...\n'; sleep 20; printf '*** Started\n\n'; cd $SCRIPTS_PATH; bash r8.sh" C-m

# Start iperf3 server on h83
tmux send-keys -t 5 "printf '\n*** Starting iperf3 server...\n'; sleep 10; printf '*** Started\n\n'; cd $SCRIPTS_PATH; bash h83.sh" C-m

# Start iperf3 server on h11
tmux send-keys -t 4 "printf '\n*** Starting iperf3 client...\n'; sleep 50; printf '*** Started\n\n'; cd $SCRIPTS_PATH; bash h13.sh" C-m

# Start the controller
tmux send-keys -t 1 "printf '\n*** Starting controller...\n'; sleep 30; printf '*** Started\n\n'; cd $SCRIPTS_PATH; bash controller.sh" C-m

tmux attach -t mn
#tmux send-keys -t 0 "cd /opt/lmg/mininet/8routers-isis-ipv6; python isis8d.py" C-m

#  bash m r5; while true; do if [ $? == 0 ]; then break; fi; sleep 1; done;


# tmux new-session -d -s mn -n ss bash

# tmux new-window -t mn -n mn-cli bash
# tmux select-pane -t 0 -T mn-cli

# tmux select-pane -t 0
# tmux split-window -v -t mn bash
# tmux select-pane -t 1 -T mn-controller

# tmux select-pane -t 1
# tmux split-window -v -t mn bash
# tmux select-pane -t 2 -T mn-r1


# tmux set -g pane-border-status bottom
