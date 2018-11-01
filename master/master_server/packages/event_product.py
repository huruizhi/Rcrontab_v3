import pika


class EventProduct:
    def __init__(self, exchange='events'):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.0.157'))
        self.channel = connection.channel()
        self.exchange = exchange
        # 广播消息
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='fanout')

    def broadcast_message(self, message):
        self.channel.basic_publish(exchange=self.exchange, routing_key='', body=message)

    def close(self):
        self.channel.close()


class TableEventProduct:
    def __init__(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.0.157'))
        self.channel = connection.channel()

        # 广播消息
        self.channel.exchange_declare(exchange='table_events', exchange_type='fanout')

    def broadcast_message(self, message):
        self.channel.basic_publish(exchange='table_events', routing_key='', body=message)

    def close(self):
        self.channel.close()


if __name__ == '__main__':
    a = TableEventProduct()
    a.broadcast_message('')
    a.close()
