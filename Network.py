# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 20:15:11 2018

@author : amine BENABDALLAH
@author  : khalid MAJDOUB
"""

from Node import Node
import time
import random
import math
import sys
from CountComplx import CountComplx


class Network():    
    """    
    This class simulates the network. 
    
    Attributes
    ----------
    nodes : dict
        List of nodes.
        
    failureRate : float
        Failure rate in the network, number of failures per second.
        
    activityRate : float
        Activity rate in the network, number of times per second a node
        asks for priviledge.
        
    terminate : bool
        Flag than indicates the state of the network, set to false to
        stop the network.
    
    Methods
    -------
    addNode() :
        Add node to the network.
        
    start():
        Start the network.
        
    stop():
        Stops the network.
    """
    def __init__(self, failureRate = 1e-4, activityRate = .05): 
    
        self.nodes = {}
        
        self.failureRate = failureRate
        
        self.activityRate = activityRate
        
        self.terminate = False
        
        
        
        
    def addNode(self, nodeId, holderId = None, askingPrivRate = None):
        """    
        Extended description of function.
        
        This function adds a node to the network and connect it to its holder.

        Parameters
        ----------
        nodeId : int 
            The id of the node.
        
        holderId : int
            The id of the node holder.
    
        Returns
        -------
        This function returns no value.
    
        """        
        if nodeId in [nid for nid in self.nodes] :
            
            raise NameError('node id must be unique !')
            
            sys.exit(0)
            
        else :
            
            if askingPrivRate is None :
                
                askingPrivRate = self.activityRate
                
            self.nodes[nodeId] = Node(nodeId, holderId, askingPrivRate)
            
            if holderId :
                
                self.nodes[nodeId].neighborsId.append(holderId)    
                
                self.nodes[holderId].neighborsId.append(nodeId)
            
    
    
    
    def next_time(self):
        """    
        Extended description of function.
        
        This function samples from an exponential distribution 
        to simulate next time a node will fail.
        
        Parameters
        ----------
        This function takes no argument.
    
        Returns
        -------
        This function returns a float.
    
        """        
        return -math.log(1.0 - random.random()) / self.failureRate
    
    
    
    def start(self):
        """    
        Extended description of function.
        
        This function starts all the nodes and pick one of them
        randomly from time to time and make fail. To simulate behaviour 
        of a real network.
        
        Parameters
        ----------
        This function takes no argument.
    
        Returns
        -------
        This function returns a float.
    
        """       
        nodesIds = list( self.nodes.keys() )
        
        randomNode = self.nodes[nodesIds[0]]
        
        for node in self.nodes.values() :
            
            node.daemon = True
            
            node.start()
        
        if self.failureRate :
        
            t = time.clock()
            
            failureTime = self.next_time()
        
        while not self.terminate :
            
            if self.failureRate and not randomNode.inRecovery.isSet() and time.clock() - t > failureTime :
                
                randomNodeId = nodesIds[random.randint(0, len(self.nodes)-1)]
                
                randomNode = self.nodes[randomNodeId]
                
                randomNode.fail()
                
                t = time.clock()
                
                failureTime = self.next_time()
                
            time.sleep(.2)
        
        
        
        
    def stop(self):
        """    
        Extended description of function.
        
        This function stops the network and send terminate signal
        to its nodes.
        
        Parameters
        ----------
        This function takes no argument.
    
        Returns
        -------
        This function returns a float.
    
        """
        print('Stopping network ...')
        
        self.terminate = True
        
        for node in self.nodes.values() :
            
            node.terminate.set()
        return CountComplx.countMsg, CountComplx.countAskP
        
        print('network stopped successfully')
            
            
