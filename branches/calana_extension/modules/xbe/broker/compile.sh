#!/bin/bash

/usr/bin/modulecmd bash load lib/smc/5.0.0

java -jar /p/hpc/soft/smc/5.0.0/bin/Smc.jar -python BrokerDispatcher.sm
java -jar /p/hpc/soft/smc/5.0.0/bin/Smc.jar -graph BrokerDispatcher.sm
dot -Tpng -o BrokerDispatcher_sm.png BrokerDispatcher_sm.dot
