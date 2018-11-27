# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 20:15:11 2018

@author  : khalid MAJDOUB
@author : amine BENABDALLAH

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
        Python dicionary containing the list of nodes.
        
    failureRate : float
        Failure rate in the network, number of failures per second.
        
    activityRate : float
        Activity rate in the network, number of times per second a node
        asks for priviledge.
        
    terminate : bool
        A flag that indicates the state of the network, it is set to false to
        stop the network.
    
    Methods
    -------
    addNode() :
        Add a node to the network.
        
    start():
        Starts the network. And randomly make a node fail according to exponential 
        distribution.
        
    stop():
        Stops the network. And collects complexity data.
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
            
            #if the id given already exists raise error 
            raise NameError('node id must be unique !')
            
            sys.exit(0)
            
        else :
            
            if askingPrivRate is None :
                
                #if no askinPrivRate is specified for the node, initialise it with the activityRate of network
                askingPrivRate = self.activityRate
            
            #instantiate the node and add it to the dicionary under the key = nodeId
            self.nodes[nodeId] = Node(nodeId, holderId, askingPrivRate)
            
            if holderId :
                
                #if holder id of the node is specified add it to the node neighbors and
                #add the node to the holder neighbors
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
        
        #start the nodes as deamon threads
        for node in self.nodes.values() :
            
            node.daemon = True
            
            node.start()
        
        if self.failureRate :
        
            t = time.clock()
            
            failureTime = self.next_time()
        
        while not self.terminate :
            
            if self.failureRate and not randomNode.inRecovery.isSet() and time.clock() - t > failureTime :
                
                #if the last failed node is out of recovery mode and next time of failure
                #is surpassed, pick up a randome node from the dictionary and make it fail
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
        
        #Before stopping the network set terminate signal of the nodes and return the complexity 
        for node in self.nodes.values() :
            
            node.terminate.set()
            
            print('network stopped successfully')
            
        return CountComplx.countMsg, CountComplx.countAskP
        
        
            
            
