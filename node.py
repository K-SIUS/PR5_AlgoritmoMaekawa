from threading import Event, Thread, Timer
from datetime import datetime, timedelta
import time
from nodeServer import NodeServer
from nodeSend import NodeSend
from message import Message
from enum_type import STATE, MSG_TYPE
from random import randint
from math import ceil, sqrt
import config
class Node():
    def __init__(self,id):
        Thread.__init__(self)
        self.id = id
        #acordarse que es var_state y no state, ese invoca al método
        self.var_state = STATE.INIT
        self.port = config.port+id
        self.daemon = True
        self.lamport_ts = 0

        #atributos gestión de votaciones
        self.has_voted = False
        self.voted_request = None
        self.request_queue = []


        self.server = NodeServer(self)
        self.server.start()
        
        if id % 2 == 0:
            self.collegues = list(range(0,config.numNodes,2))
        else:
            self.collegues = list(range(1,config.numNodes,2))

        self.client = NodeSend(self)   
        self.time_request_cs = None 
        self.time_exit_cs = None
        
        self.signal_request_cs = Event()
        self.signal_request_cs.set()
        self.signal_enter_cs = Event()
        self.signal_exit_cs = Event()   
        #attributess as a proposer (propose & send request)
        self.voting_set = self._create_voting_set()
        self.num_votes_received = 0
        self.has_inquired = False

    #estas funciones son necesarias para el funcionamiento de las
    #llamadas en state.
    #crea la votación para un nodo específico
    def _create_voting_set(self):
        voting_set = dict()
        mat_k = int(ceil(sqrt(config.numNodes)))
        (row_id, col_id) = (int(self.id / mat_k), 
                            int(self.id % mat_k))
        for i in range(mat_k):
            voting_set[mat_k * row_id + i] = None
            voting_set[col_id + mat_k * i] = None
        return voting_set
    
    #manda petición multicast a los votantes del nodo cuando se ejecute
    def request_cs(self, ts):
        self.var_state = STATE.REQUEST
        self.lamport_ts += 1
        
        request_msg = Message(msg_type=MSG_TYPE.REQUEST,
                              src=self.id,
                              data = "Request CS")
        print("petición para entrar en CS del Nodo %i"%self.id)
        self.client.multicast(request_msg, self.voting_set)
        #libera las peticiones signal
        self.signal_request_cs.clear()
    
    #actualiza el estado del nodo y está en región crítica durante
    #un tiempo aleatorio 
    def enter_cs(self, ts):
        self.time_exit_cs = ts + timedelta(milliseconds=randint(5, 10))
        self.var_state = STATE.HELD
        self.lamport_ts += 1
        self.signal_enter_cs.clear()


    def exit_cs(self, ts):
        self.time_request_cs = ts + timedelta(milliseconds=randint(10, 20)) 
        self.var_state = STATE.RELEASE
        self.lamport_ts += 1
        self.num_votes_received = 0
        print("Node %i leaving CS"%self.id)
        release_msg = Message(msg_type=MSG_TYPE.RELEASE,
                              src=self.id,
                              data = "Leaving CS")
        self.client.multicast(release_msg, self.voting_set)
        self.signal_exit_cs.clear()
    

    def do_connections(self):
        self.client.build_connection()

    def state(self):
        timer = Timer(1, self.state)
        timer.start()
        self.curr_time = datetime.now()
        #wakeup
        #DO shomething
        #checkeamos el estado del nodo

        if (self.state == STATE.RELEASE and 
                self.time_request_cs <= self.curr_time):
            print("***entro en if1***\n")
            if not self.signal_request_cs.is_set():
                print("***entro en if2***\n")
                self.signal_request_cs.set()
        elif (self.state == STATE.REQUEST and 
                self.num_votes_received == len(self.voting_set)):
            print("***entro en if3***\n")
            if not self.signal_enter_cs.is_set():
                print("***entro en if4***\n")
                self.signal_enter_cs.set()
        elif (self.state == STATE.HELD and 
                self.time_exit_cs <= self.curr_time):
            print("***entro en if5***\n")
            if not self.signal_exit_cs.is_set():
                print("***entro en if6***\n")
                self.signal_exit_cs.set()  
     
      
        self.wakeupcounter += 1
        if self.wakeupcounter == 2:
            timer.cancel()
            print("Stopping N%i"%self.id)
            self.daemon = False
            
        else:
            print("This is Node_%i at TS:%i sending a message to my collegues"%(self.id,self.lamport_ts))

            message = Message(msg_type="greetings",
                            src=self.id,
                            data="Hola, this is Node_%i _ counter:%i"%(self.id,self.wakeupcounter))

            self.client.multicast(message, self.collegues)
       
    def run(self):
        print("Run Node%i with the follows %s"%(self.id,self.collegues))
        self.client.start()
        self.wakeupcounter = 0
        self.state()

