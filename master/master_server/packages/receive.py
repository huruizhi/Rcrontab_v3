import pika


class ReceiveRabbitMQMessage:
    def __init__(self, name, target=None):
        name = str(name)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.0.156'))
        self.channel = connection.channel()
        self.channel.exchange_declare(exchange='events', exchange_type='fanout')
        result = self.channel.queue_declare(queue=name)
        self.channel.queue_bind(exchange='events', queue=name)
        if target:
            self.callback = target
            self.channel.basic_consume(self.callback, queue=name, no_ack=True)

    @staticmethod
    def callback(ch, method, properties, body):
        raise Exception("No method")

    def start(self):
        self.channel.start_consuming()