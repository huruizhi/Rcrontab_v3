from master_server.models import ServerInfo
from master_server.packages.mysql_check import connection_usable
from urllib import request, parse
import time


def slave_exec_api(sid, api, version, subversion=None):
    """
    查询API所在的服务器，并返回url
    :return:
    """
    if not subversion:
        subversion = int(time.time()) * 1000

    connection_usable()
    parameter_str = "?sid={sid}&version={version}&subversion={subversion}".format(sid=sid,
                                                                                  version=version,
                                                                                  subversion=subversion)
    api = api + parameter_str
    data = {
        'url': api,
    }

    try:
        server = ServerInfo.objects.get(path__program__sid=sid)
        ip = server.ip
        port = server.port
        url = "http://{ip}:{port}/slave_server/exec_api/".format(ip=ip, port=port)
    except Exception as e:
        page = 'Can not find server ip port!'
        return api, page
    try:
        data = parse.urlencode(data).encode('utf-8')
        req = request.Request(url, data=data)
        page = request.urlopen(req).read()
        page = page.decode('utf-8')
        return api, page
    except Exception as e:
        return api, e


