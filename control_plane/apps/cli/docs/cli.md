**Command-Line Reference**
----

This folder contains the documentation of the Command-Line Interface (CLI) for the Controller.

The CLI can be started with the default configuration by typing the command **controller** in the Python environment where you installed it:
```console
$ controller
```

Optionally, you can pass a configuration file containing your settings:
```console
$ controller --env-file config/controller.env
```

The Controller CLI will start and load the configuration:
```console
INFO:apps.cli.cli:*** Loading configuration from /home/rose/.envs/controller-venv/lib/python3.8/site-packages/rose_srv6_control_plane_controller-0.0.1-py3.8.egg/controller/cli/../config/controller.env
INFO:root:SERVER_DEBUG: False
INFO:apps.cli.cli:*** Validating configuration

****************** CONFIGURATION ******************

ArangoDB URL: http://localhost:8529
ArangoDB username: root
ArangoDB password: ************
Kafka servers: kafka:9092
Enable debug: False

***************************************************


Welcome! Type ? to list commands
controller> 
```

Now the CLI is ready to receive commands. For a list of the available commands, you can check the documentation in this folder or type the **help** command:
```
controller> help
```

* Description of the interactive CLI : ```help```
* Exit from the CLI : ```exit```
* [SRv6 functions](docs/srv6.md) : ```help```
* [SRv6 Performance Measurement functions](docs/srv6pm.md) : ```help```
* [Topology utilities](docs/topology.md) : ```topology```
