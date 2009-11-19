#!/bin/bash

/usr/bin/modulecmd bash load lib/smc/5.0.0

java -jar /p/hpc/soft/smc/5.0.0/bin/Smc.jar -python BrokerDispatcher.sm
sed -e 's%statemap.FSMContext.__init__(self)%statemap.FSMContext.__init__(self, BrokerDispatcherFSM.StInitial)%' BrokerDispatcher_sm.py > dummy
mv dummy BrokerDispatcher_sm.py

java -jar /p/hpc/soft/smc/5.0.0/bin/Smc.jar -graph BrokerDispatcher.sm
dot -Tpng -o BrokerDispatcher_sm.png BrokerDispatcher_sm.dot


## job State Machine
java -jar /p/hpc/soft/smc/5.0.0/bin/Smc.jar -python JobStateMachine.sm
sed -e 's%statemap.FSMContext.__init__(self)%statemap.FSMContext.__init__(self, JobFSM.StPendingNew)%' JobStateMachine_sm.py > dummy
mv dummy JobStateMachine_sm.py
java -jar /p/hpc/soft/smc/5.0.0/bin/Smc.jar -graph JobStateMachine.sm
dot -Tpng -o JobStateMachine_sm.png JobStateMachine_sm.dot
