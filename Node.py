# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 20:15:11 2018

@author : amine BENABDALLAH
@author  : khalid MAJDOUB
"""

from collections import deque
import threading
import pika
import time 
import random
import math
import traceback
from CountComplx import CountComplx
    
class MsgType:
    """    
    This class gathers the constants that'll represent the message type.
    
    Attributes
    ----------
    No attributes.
    
    Methods
    -------
    No methodes.
    """
    REQUEST = 'R'
    ASSIGN  = 'A'
    RESTART = 'S'
    ADVISE  = 'D'


class Ressource():
    """    
    Is used to simulate the real use of a ressource in a concurrent context.
    If more than one node at time tries to access the ressource an exception is raised.
    
    Attributes
    ----------
    
    acquired : bool 
        A flag to represent the state of the ressource.
        
    Methods
    -------
    
    acquire() 
        Sets the state of ressource to acquired.
        
    release()
        Sets the state of ressource to available.
    """    
    acquired = False
    
    @staticmethod
    def acquire():
        
        if not Ressource.acquired :
            
            Ressource.acquired = True
            
        else :
            
            raise Exception('Ressource already acquired!') 
            
    @staticmethod
    def release():
        
        Ressource.acquired = False



class Node(threading.Thread):
    """
    This class is used to simulate a node
    
    Attributes
    ----------
    askingPrivRate : float
        The number of times per second the node will ask for privilege (.2 per default)
       
    id : int
        The node id
       
    neighborsId : list
        A list that contains the neighbors ids of a node
       
    inRecovery : threading.Event
        Threading signal that indicates if the node is in recovery state
       
    neighborHolderId : dict
        The id of the  neighbors holders nodes
       
    inNeighborReqQ : dict
        Booleans that holds the information about the node being in the requestQ of 
        its neighbors
       
    recievedFrom : dict
        A boolean by neighbor set to true when an advise message is received 
        from that neighbor
       
    neighborAsked : dict
        Stores the asked attribute of neighbors received in advise messages
       
    holderId : int
        The id of the node holder
    
    using : bool
        A boolean that indicates if the node is in the critical section
    
    asked : bool
        A boolean that indicates if the node has asked
    
    teminate : threading.Event
        Threading signal that indicate if node should continue to work
    
    canWork : threading.RLock
        Reantrant lock to synchronise the main Thread and the listner
        
    requestQ : deque
        A queue object to store the ids of request senders
        
    connection : pika.BlockingConnection
        RabbitMQ blocking connection
    
    channel : pika.BlockingConnection.channel
        The node's rabbitMQ connection channel
       
    Methods
    -------
    listen()
        A methdod to consume received messages from rabbitMQ channel
       
    nextTime()
        Time to wait before asking for privilege next time
       
    callback()
        This methode is called when a message is received
       
    assign_privilege()
        This function assign the privilege to the node or forward assign msg
       
    recover()
        Recovers the node attributes to the state before failure
    
    send_message()
        This function sends a Message to a node
    
    make_request()
        This function sends a Message of type Request to the holder
        
    fail()
        This function simulate node failure
    
    run()
        This methode simulate the behaviour of the node in the network.
      
    """   

    def __init__(self, id, holderId = None, askingPrivRate = .05): 
    
        threading.Thread.__init__(self) 
        
        self.askingPrivRate = askingPrivRate
        
        self.id = id
        
        self.neighborsId = []
        
        self.requestQ = deque([])
        
        if holderId is None : 
    
            self.holderId = self.id
            
        else : 
    
            self.holderId = holderId 
    
        self.using = False 
    
        self.asked = False 
        
        self.inRecovery = threading.Event()
        
        self.terminate = threading.Event()
        
        self.canWork = threading.RLock()
        

    def listen(self):
        """    
        Extended description of function.
        
        This function performs the listening rootine of rabbitMQ
        and calls the methode callback when a message is dequeued. 
        It is executed in a separeted Thread.
        
        Parameters
        ----------
        This function takes no argument.
    
        Returns
        -------
        This function returns no value.
    
        """        
        self.channel.basic_consume(self.callback, queue = 'channel'+ str(self.id), no_ack=True) 
        
        self.channel.start_consuming() 
        
    
    def next_time(self):
        """    
        Extended description of function.
        
        This function samples from an exponential distribution 
        to simulate next time node will ask for privilege.
        
        Parameters
        ----------
        This function takes no argument.
    
        Returns
        -------
        This function returns a float.
    
        """
        return -math.log(1.0 - random.random()) / self.askingPrivRate  


    def callback(self, ch, method, properties, body): 
        """    
        
        Extended description of function.
        
        This function is called whenever the node receives a message.
        The message is decomposed and traitements are done 
        depending on its type.
        
        There is 4 types of messages exchanged in the network :
        
        Request message : is sent by the node to its holder to ask for privilege, then the message is
        propagated throughout the tree until it reaches the privileged node.
        
        Format : 'R' | '*' | node id  
        
        Assign message : is forwarded from the privileged node to the one asked for privilege. During 
        that process the structure of the tree is reversed.
        
        Format :  'A' | '*' | node id
        
        Restart message: is sent by the node to its neighbors in the recovery phase, 
        asking them to send back, those informations will be usded by the node
        to reconstruct its state before faillure.
        
        Format : 'S' | '*' | node id 
            
        Advise message : the response of neighbors to the node in recovery
        containing informations about their current state.
        
        Format : 'D'|'*'|node id|'*'|senderHolderId |','|inSenderReqQ|','|senderAsked 
            
        Parameters
        ----------
        
        body : str
            byte string containing the body of the message
    
        Returns
        -------
        This function returns no argument. 
        
        """ 
        msgBody = body.decode()   

        msgType, senderId, msg = msgBody.split('*')     
        
        senderId = int(senderId)
        
        if msgType == MsgType.REQUEST :
            
            print(self.id, 'received request from', senderId)
            
            self.requestQ.append(senderId)
            
        elif msgType == MsgType.ASSIGN :
            
            print(self.id, 'received assign from', senderId)
            
            self.holderId = self.id
            
        elif msgType == MsgType.RESTART :
            
            print(self.id, 'received restart from', senderId)
            
            msg = str(self.holderId)+','+str(senderId in self.requestQ)+','+str(self.asked)
            
            self.send_message(MsgType.ADVISE, senderId, msg)
            
        elif msgType == MsgType.ADVISE :
            
            print(self.id, 'received advise from', senderId)
            
            senderHolderId , inSenderReqQ, senderAsked = msg.split(',')
            
            senderHolderId = int(senderHolderId)
            
            inSenderReqQ = (inSenderReqQ == 'True') 
            
            senderAsked = ( senderAsked == 'True')
            
            self.inNeighborReqQ[senderId] = inSenderReqQ
            
            self.neighborHolderId[senderId] = senderHolderId
            
            self.recievedFrom[senderId] = True
            
            self.neighborAsked[senderId] = senderAsked
            
            if all( value for value in self.recievedFrom.values() ) :
                
                self.recover()
                
        if not self.inRecovery.isSet() :
            
            self.assign_privilege()
            
            self.make_request()
            
    def recover(self):
        
        """    
        
        Extended description of function.
        
        After receiving advise message from all node neighbors, this function is called
        to reconstruct from informations gathered its state before faillure.
        
        Parameters
        ----------
        This function takes no parameters.
    
        Returns
        -------
        This function returns no value.
        
        """ 
        
        if all(id == self.id for id in self.neighborHolderId.values()) :
            
            self.holderId = self.id
            
            self.asked = False
            
        else :
            
            for idN, idNH in self.neighborHolderId.items() :
                
                if idNH != self.id :
                    
                    self.holderId = idN
                    
                    self.asked = self.inNeighborReqQ[idN]
                    
                    break
        
        for nId in self.neighborsId :
            
            if self.neighborHolderId[nId] == self.id and self.neighborAsked[nId] :
                
                self.requestQ.append(nId)
                
        self.inRecovery.clear()
        
        print('node ', self.id, ' left recovery mode -->>')
        
                        
                        
    def assign_privilege(self): 
        """    
        Extended description of function.
        
        This function either assignes the privilege to the node 
        in the case it is the root of the tree, or forwards an ASSIGN
        type message to the first one to enter the request queue of 
        the node.
        
        Assigne priveledge message format :  'A' | '*' | id of node 
            
        
        Parameters
        ----------
        This function takes no parameters.
    
        Returns
        -------
        This function returns no value.
    
        """
        with self.canWork :
            
            if self.holderId == self.id and not self.using and self.requestQ :
                
                print( self.id, " is assigning privilege" )
                
                self.holderId = self.requestQ.popleft()
        
                self.asked = False 
        
                if self.holderId == self.id : 
        
                    self.using = True 
                    
                    print (str(self.id) + " enter the critical section <<--")
                    
                    Ressource.acquire() #hold ressource
                    
                    time.sleep(1.5) #consume ressource                
                    
                    Ressource.release() #release ressource
                    
                    print (str(self.id) + " left the critical section  -->>")
                    
                    self.using = False
                    
                    if not self.inRecovery.isSet() :
                        
                        self.assign_privilege()
                        
                        self.make_request()
                    
                elif not self.inRecovery.isSet() :
                
                    self.send_message(MsgType.ASSIGN, self.holderId)




    def send_message(self, msgType, dest, msgBody = ''):
        
        """       
        Extended description of function.
        
        This function joins the arguments given in a string and then sends it to the destination node.
        It is based on a rabbitMQ rootine (basic_publish).
        
        Message format : msgType | '*' | node id | '*' | msgBody
        
        Parameters
        ----------
        
        msgType : str 
            A constant refering to the type of the message to be sent 
            
        dest : str 
            A string containing the id of the receiver
            
        msgBody : str
            A string containing the body of the message. This argument is optional (is set to '' by default) 
    
        Returns
        -------
        
        This function returns no value.
        
        """ 
        CountComplx.countMsg+=1

        self.channel.basic_publish(exchange='', 
        routing_key='channel' + str(dest), 
        body = msgType +'*'+ str(self.id) + '*' + msgBody)
        
        
    def fail(self):
        """
        
        Extended description of function.
        
        This function is called to simulate failure of the node. It resets its 
        attributes, set the inRecovery signal, waits for 5 secs then sends a
        restart message to its neighbors
        
        Parameters
        ----------
        This function takes no parameters
        
        Returns
        -------
        This function returns no value
        
        """          
        self.inRecovery.set()
        
        self.asked = False
        
        self.requestQ.clear()
        
        self.using = False
        
        self.holderId = None
        
        self.neighborHolderId = {}
         
        self.inNeighborReqQ = {}
        
        self.neighborAsked = {}
        
        self.recievedFrom = { nId : False for nId in self.neighborsId }
        
        print('node ', self.id, ' failed!!!')
        
        time.sleep(5)
        
        print('node ', self.id, ' is in recovery mode <<---')
        
        for neighborId in self.neighborsId :
            
            self.send_message(MsgType.RESTART, neighborId)        
   
     
    def make_request(self): 
        """
        
        Extended description of function.
        
        This function is called by the node either to ask for the privilege, or to forward
        the request to the rest of the tree.
        
        Request message format :   'R' | '*' | node id  
    
        Parameters
        ----------
        This function takes no parameters.
    
        Returns
        -------
        This function returns no value. 
        
        """ 
        with self.canWork :
            
            if self.holderId != self.id and self.requestQ and not self.asked : 
            
                print(self.id, " is sending request to ", self.holderId)
                
                self.send_message(MsgType.REQUEST, self.holderId)
                
                self.asked = True 


                
    def run(self): 
        """    
        Extended description of function.
        
        This function simulate the behaviour of the node in the network. After waiting a certain
        time sampled from an exponential distribution, the node asks for privilege. Then waits to 
        be served before asking again.
        
        Parameters
        ----------
        This function takes no argument.
    
        Returns
        -------
        This function returns no value.
    
        """
        
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) 
    
        self.channel = self.connection.channel() 
        
        self.channel.queue_declare(queue = 'channel'+ str(self.id) ) 
        
        threadRMQ = threading.Thread(target = self.listen)
        
        threadRMQ.daemon = True
        
        threadRMQ.start()
        
        try :
            
            while not self.terminate.isSet() :
                
                if self.askingPrivRate > 0:
                
                    time.sleep(self.next_time())
                    
                    if self.id not in self.requestQ and not self.inRecovery.isSet():
                        
                        print(str(self.id) + " is asking for privilege")
                        
                        CountComplx.countAskP+=1
                        
                        self.requestQ.append(self.id)
                        
                        self.assign_privilege()
                        
                        self.make_request() 
                    
                time.sleep(.2)
        
            self.connection.close()
                    
        except Exception :
            
            traceback.print_exc()
        
        print(self.id, ' is done')
        






            




