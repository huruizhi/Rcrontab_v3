import pika


class ReceiveRabbitMQMessage:
    def __init__(self, name, target=None, exchange=None):
        if exchange is None:
            exchange = 'events'
        name = str(name)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.0.157',
                                                                       heartbeat_interval=60,))
        self.channel = connection.channel()
        self.channel.exchange_declare(exchange=exchange, exchange_type='fanout')
        result = self.channel.queue_declare(queue=name)
        self.channel.queue_bind(exchange=exchange, queue=name)
        if target:
            self.callback = target
            self.channel.basic_consume(self.callback, queue=name)

    @staticmethod
    def callback(ch, method, properties, body):
        raise Exception("No method")

    def start(self):
        self.channel.start_consuming()
