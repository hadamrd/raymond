from Network import Network
import sys

failureRate = float(input('enter failure rate : '))

activityRate = float(input('enter activity rate : '))

network = Network(failureRate, activityRate)

network.addNode(3)

network.addNode(4, 3)

network.addNode(2, 3)

network.addNode(1, 2)

network.addNode(5, 3)

try :
    
    network.start()
    
except KeyboardInterrupt:
    
    network.stop()
    
    sys.exit(0)


