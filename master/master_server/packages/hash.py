import hashlib
import json
import time


def get_hash(string):
    try:
        string = json.dumps(string)
        string = str(time.time()) + string
        return hashlib.md5(string.encode('utf-8')).hexdigest()[8:-8]
    except Exception as e:
        string = json.dumps(time.time())
        return hashlib.md5(string.encode('utf-8')).hexdigest()[8:-8]
