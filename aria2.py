import xmlrpc.client as rpc
import time
import json
s = rpc.ServerProxy('http://localhost:6888/rpc')
gid = s.aria2.addUri([r'https://dl.softmgr.qq.com/original/im/QQ9.3.8.27381.exe'])
for i in range(100):
    time.sleep(1)
    print(s.aria2.tellStatus(gid, ['completedLength','totalLength','downloadSpeed']))
    # json.