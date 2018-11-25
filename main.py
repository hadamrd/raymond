from Network import Network
import sys

#failureRate = float(input('enter failure rate : '))
#
#activityRate = float(input('enter activity rate : '))

network = Network(failureRate = 0.0 , activityRate = .05)

network.addNode(5)

network.addNode(7, 5)

network.addNode(3, 5)

network.addNode(9, 5)

network.addNode(8, 7)

network.addNode(6, 7)

network.addNode(10, 9)

network.addNode(4, 3)

network.addNode(2, 3)

network.addNode(1, 2)

network.addNode(11, 5)

network.addNode(14, 11)

network.addNode(12, 11)

network.addNode(13, 7)

network.addNode(15, 1)

network.addNode(16, 15)

network.addNode(18, 5)

network.addNode(17, 8)

try :
    
    network.start()
    
except KeyboardInterrupt:
    
    cMsg, cAskP = network.stop()
    
    print('la complexite estimee est : ', cMsg/cAskP)
    
    sys.exit(0)


