import pika
import uuid
import threading
import sys
import time

class Noeud:
    def __init__(self, self_id, holder_id, neighbours, self_response_queue, self_messaging_queue):
        self.self_id = self_id
        self.holder_id = holder_id
        self.neighbours = neighbours
        self.self_response_queue = self_response_queue
        self.self_messaging_queue = self_messaging_queue
        self.client = Client(self)
        self.thread_input = threading.Thread(target=self.read_keyboard)
        self.thread_input.daemon = True
        self.thread_input.start()
        self.serveur = Serveur(self.client)

    def read_keyboard(self):
        while 1:
            sys.stdin.readline()
            print('[ASK] Requesting [' + self.holder_id + ']')
            try:
                self.client.ask_for_token()
            except Exception:
                print(
                    '[ERROR] RabbitMQ has appearently restarted connections, please rerun the program...')

class Client:
    def __init__(self, noeud):
        self.noeud = noeud
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        self.initialized = False
        self.channel = self.connection.channel()
        if self.noeud.holder_id != '':
            self.initialized = True
            for neighbour in self.noeud.neighbours:
                print '[INIT] TO [' + neighbour + ']'
                self.channel.queue_declare(queue=self.noeud.neighbours[neighbour])
                self.channel.basic_publish(exchange='',
                                           routing_key=self.noeud.neighbours[neighbour],
                                           body='INIT ' + self.noeud.self_id)
        self.channel.queue_declare(queue=self.noeud.self_response_queue)
        self.callback_queue = self.noeud.self_response_queue

        self.channel.basic_consume(self.on_response,
                                   queue=self.callback_queue)
        self.corr_id_holder = None
        self.corr_id_self = None

    def on_response(self, ch, method, props, body):
        if self.corr_id_holder == props.correlation_id:
            self.response_to_forwarding = body
        elif self.corr_id_self == props.correlation_id:
            self.response_to_asking = body
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def forward_request_for_token(self):
        self.response_to_forwarding = None
        self.corr_id_holder = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self.noeud.neighbours[self.noeud.holder_id],
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id_holder,
                                   ),
                                   body='REQUEST ' + self.noeud.self_id)
        while self.response_to_forwarding is None:
            self.connection.process_data_events()
            time.sleep(.1)
        return self.response_to_forwarding

    def ask_for_token(self):
        self.response_to_asking = None
        self.corr_id_self = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self.noeud.self_messaging_queue,
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id_self,
                                   ),
                                   body='REQUEST ' + self.noeud.self_id)
        while self.response_to_asking is None:
            self.connection.process_data_events()
            time.sleep(.1)
        return self.response_to_asking

class Serveur:
    def __init__(self, client):
        self.client = client
        self.noeud = self.client.noeud
        self.restarting = self.noeud.neighbours.copy()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.noeud.self_messaging_queue)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            self.incoming_requests_management, queue=self.noeud.self_messaging_queue)

        if client.initialized == True:
            print('[START] Node started, Press Enter to ask for privilege')
        else:
            print('[INIT] WAITING (PRESS ENTER IF RESTARTING)')
        self.channel.start_consuming()

    def incoming_requests_management(self, ch, method, props, body):
        asker = body.split(' ')[1]
        if 'INIT' in body:
            self.noeud.holder_id = asker
            self.client.initialized = True
            print '[INIT] FROM [' + asker + ']'
            print('[START] Node started, Press Enter to ask for privilege')
            for neighbour in self.noeud.neighbours:
                if neighbour != self.noeud.holder_id:
                    print '[INIT] TO [' + neighbour + ']'
                    ch.queue_declare(queue=self.noeud.neighbours[neighbour])
                    ch.basic_publish(exchange='',
                                     routing_key=self.noeud.neighbours[neighbour],
                                     body='INIT ' + self.noeud.self_id)
        elif 'RESTART' in body:
            print '[RESTART] TO [' + asker + ']'
            if self.noeud.holder_id != asker:
                ch.basic_publish(exchange='',
                                 routing_key=self.noeud.neighbours[asker],
                                 body='HOLDER ' + self.noeud.self_id)
            elif self.noeud.holder_id == asker:
                ch.basic_publish(exchange='',
                                 routing_key=self.noeud.neighbours[asker],
                                 body='NOCHANGE ' + self.noeud.self_id)
        elif 'HOLDER' in body:
            self.noeud.holder_id = asker
            print '[RESTART] COMPLETED'
        elif 'NOCHANGE' in body:
            print '[NOCHANGE] FROM [' + asker + ']'
            self.restarting.pop(asker)
            if len(self.restarting) != 0:
                ch.basic_publish(exchange='',
                                routing_key=self.restarting.items()[0][1],
                                body='RESTART ' + self.noeud.self_id)
            else:
                self.noeud.holder_id = self.noeud.self_id
                print '[TOKEN] Regenerating'
        elif 'REQUEST' in body and self.noeud.holder_id != '':
            print('[REQUEST] From [' + asker + ']')
            if self.noeud.holder_id == self.noeud.self_id:
                ch.basic_publish(exchange='',
                                 routing_key=props.reply_to,
                                 properties=pika.BasicProperties(
                                     correlation_id=props.correlation_id),
                                 body='Token')
                print '[TOKEN] Sent to [' + asker + ']'
            else:
                response = self.client.forward_request_for_token()
                print '[FORWARDING] ' + response
                ch.basic_publish(exchange='',
                                    routing_key=props.reply_to,
                                    properties=pika.BasicProperties(
                                        correlation_id=props.correlation_id),
                                     body=response)
            self.noeud.holder_id = asker
            if asker == self.noeud.self_id:
                print '[CRITICAL] Entering'
                time.sleep(10)
                print '[CRITICAL] Leaving'
        else:
            print '[INIT] ERROR'
            print '[RESTART] TO [' + asker + ']'
            if asker != self.noeud.self_id:
                ch.basic_publish(exchange='',
                                routing_key=self.noeud.neighbours[asker],
                                body='RESTART ' + self.noeud.self_id)
            else:
                ch.basic_publish(exchange='',
                                     routing_key=props.reply_to,
                                     properties=pika.BasicProperties(
                                         correlation_id=props.correlation_id),
                                     body='ERROR')
                ch.basic_publish(exchange='',
                                routing_key=self.noeud.neighbours.items()[0][1],
                                body='RESTART ' + self.noeud.self_id)
                    
        ch.basic_ack(delivery_tag=method.delivery_tag)
