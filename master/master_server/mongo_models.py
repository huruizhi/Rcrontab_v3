import mongoengine as mn
mn.connect('mongo_test', host='192.168.0.156', port=27017)


class Post(mn.Document):
    title = mn.StringField(required=True, max_length=200)
    content = mn.StringField(required=True)
    author = mn.StringField(required=True, max_length=50)
    published = mn.DateTimeField()