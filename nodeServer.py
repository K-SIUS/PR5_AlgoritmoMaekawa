import select
from threading import Thread
import utils
from message import Message
import json
import heapq
from enum_type import MSG_TYPE, STATE


class NodeServer(Thread):
    def __init__(self, node):
        Thread.__init__(self)
        self.node = node
       
    
    
    def run(self):
        self.update()

    def update(self):
        self.connection_list = []
        self.server_socket = utils.create_server_socket(self.node.port)
        self.connection_list.append(self.server_socket)

        while self.node.daemon:
            (read_sockets, write_sockets, error_sockets) = select.select(
                self.connection_list, [], [], 5)
            if not (read_sockets or write_sockets or error_sockets):
                print('NS%i - Timed out'%self.node.id) #force to assert the while condition 
            else:
                for read_socket in read_sockets:
                    if read_socket == self.server_socket:
                        (conn, addr) = read_socket.accept()
                        self.connection_list.append(conn)
                    else:
                        try:
                            msg_stream = read_socket.recvfrom(4096)
                            for msg in msg_stream:
                                try:
                                    ms = json.loads(str(msg,"utf-8"))
                                    self.process_message(ms)
                                except:
                                    None
                        except:
                            read_socket.close()
                            self.connection_list.remove(read_socket)
                            continue
        
        self.server_socket.close()

    def process_message(self, msg):
        # Do shomething
       # print("Node_%i receive msg: %s"%(self.node.id,msg))
        
        self.node.lamport_ts = max(self.node.lamport_ts + 1, msg['ts'])
        
        if msg['msg_type'] == MSG_TYPE.REQUEST:
            print("PROCESS_REQUEST")
            self._on_request(msg)
        elif msg['msg_type']== MSG_TYPE.GRANT:
            print("PROCESS_GRANT")
            self._on_grant(msg)
        elif msg['msg_type']== MSG_TYPE.RELEASE:
            print("PROCESS_RELEASE")
            self._on_release(msg)
        elif msg['msg_type']== MSG_TYPE.FAIL:
            print("PROCESS_FAIL")
            self._on_fail(msg)
        elif msg['msg_type'] == MSG_TYPE.INQUIRE:
            print("PROCESS_INQUIRE")
            self._on_inquire(msg)
        elif msg['msg_type'] == MSG_TYPE.YIELD:
            print("PROCESS_YIELD")
            self._on_yield(msg)

    #metodo de gestion de mensajes request.
    def _on_request(self, request_msg):
             
        if self.node.var_state == STATE.HELD:
            heapq.heappush(self.node.request_queue, request_msg)
        else:
            if self.node.has_voted:
                heapq.heappush(self.node.request_queue, request_msg)
                response_msg = Message(src=self.node.id)
                if (request_msg < self.node.voted_request and 
                        not self.node.has_inquired):
                    response_msg.set_type(MSG_TYPE.INQUIRE)
                    response_msg.set_dest(self.node.voted_request['src'])
                    self.node.has_inquired = True
                else:
                    response_msg.set_type(MSG_TYPE.FAIL)
                    response_msg.set_dest(request_msg['src'])
                self.node.client.send_message(response_msg, response_msg.dest)
            else:
                self._grant_request(request_msg)
    #método que aumenta el contador de votos de un nodo
    def _on_grant(self, grant_msg):
        
        self.node.num_votes_received += 1
        print("VOTACIÓN: Votos totales recibidos de el nodo: %i: %i ha recibido un voto de Nodo: %i."%(self.node.id, self.node.num_votes_received, grant_msg['src']))

    #metodo que controla los mensajes RELEASE
    def _on_release(self, release_msg=None):
       
        #si la cola de requests no está vacía, hará un pop de la prioridad superior
        #sino resetea los flags de votación
        self.node.has_inquired = False
        if self.node.request_queue:
            print("Released from release queue\n")
            next_request = heapq.heappop(self.node.request_queue)
            self._grant_request(next_request)
        else:
            print("Reset de votación\n")
            self.node.has_voted = False
            self.node.voted_request = None
    
    #metodo que activa la petición de rección crítica
    def _grant_request(self, request_msg):
      
        print("Petición de nodo %i para que acceda a Región Crítica"%self.node.id)
        print("Región Crítica de %i"%request_msg['src'] )
        grant_msg = Message(msg_type=MSG_TYPE.GRANT,
                            src=self.node.id,
                            dest=request_msg['src'],
                            )
        self.node.client.send_message(grant_msg, grant_msg.dest)
        self.node.has_voted = True
        self.node.voted_request = request_msg
   
   #en caso de fail descartar el proceso
    def _on_fail(self, fail_msg):
        pass

    #metodo que gestiona
    def _on_inquire(self, inquire_msg):
        print("INQUIRE: petición de Nodo: %i"%self.node.id)
        if self.node.var_state != STATE.HELD:
            print("INQUIRE success, quitando voto%i"%inquire_msg['src'])
            self.node.num_votes_received -= 1
            yield_msg = Message(msg_type=MSG_TYPE.YIELD,
                                src=self.node.node.id,
                                dest=inquire_msg['src'])
            self.node.client.send_message(yield_msg, yield_msg.dest)
        
    #saca de la pila el último votado en la cola de requests 
    #y lo libera
    def _on_yield(self, yield_msg):
        print("Yield de tipo %i en el nodo i%"%(yield_msg,self.node.id))
        heapq.heappush(self.node.request_queue,
                       self.node.voted_request)
        self._on_release()