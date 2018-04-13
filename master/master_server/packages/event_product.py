import pika


class EventProduct:
    def __init__(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.0.156'))
        self.channel = connection.channel()

        # 广播消息
        self.channel.exchange_declare(exchange='events', exchange_type='fanout')

    def broadcast_message(self, message):
        self.channel.basic_publish(exchange='events', routing_key='', body=message)

    def close(self):
        self.channel.close()
