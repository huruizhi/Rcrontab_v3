import pika


class MysqlSyncMQ:
    def __init__(self):
        self.host = '120.27.245.74'
        self.port = 5672
        self.user = 'liff'
        self.passwd = 'Liff@2018'
        self.credentials = pika.PlainCredentials(self.user, self.passwd)  # 不设置的话，默认是 guest guest 账户
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                            port=self.port,
                                                                            credentials=self.credentials,
                                                                            heartbeat=60)
                                                  )
        self.channel = self.connection.channel()

    def send_message(self, message):
        properties = pika.BasicProperties(delivery_mode=2, )
        self.channel.basic_publish(exchange='',
                                   routing_key='sync_tasks',
                                   body=message,
                                   properties=properties)

    def close(self):
        self.channel.close()
