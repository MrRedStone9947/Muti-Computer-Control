class ServerCommands():
    def help(self,server):
        print('------------------------------------------')
        for c,t in command_parser.items():
            print(f'{c}:\n    {t["description"]}')
        print('------------------------------------------')
        return True
    def connectionInfo(self,server):
        if len(server.clients)<=0:
            print('当前并无连接...')
        else:
            print('--------------------------------------------------------')
            for c in server.clients:
                print(f'ID: {c.id},名称: {c.name},'
                      f'地址: {c.addr}')
            print('--------------------------------------------------------')
        return True
    def sendPlugin(self,server):
        print('正在发送插件...')
        return False
    def runPlugin(self,server):
        print('正在运行插件...')
        return False
    def reload(self,server):
        print('正在重载客户端...')
        return False
    def syncPlugins(self,server):
        print('正在同步插件...')
        for p,t in plugin_parser.items():
            if not os.path.exists(f'./plugins/{t["dir"]}'):
                print(f'插件 {p} 的对应文件 {t["dir"]} 不存在！')
        return False

class ClientCommands():
    def sendPlugin(self,client):
        file=File(client.cur_args[0],'PLUGIN')
        file.init()
        client.sendFile(file)
        return False
    def runPlugin(self,client):
        return False
    def reload(self,client):
        client.SOCKET.close()
        client.CONNECTION_CHECK_SOCKET.close()
        return True
    def syncPlugins(self,client):
        plugin_count=0
        for p,t in plugin_parser.items():
            if not os.path.exists(f'./plugins/{t["dir"]}'):
                continue
            plugin_count+=1
        message=base64.b64encode(str(plugin_count).encode(encoding='utf-8'))
        client.SOCKET.sendall(message)
        for p,t in plugin_parser.items():
            if not os.path.exists(f'./plugins/{t["dir"]}'):
                continue
            file=File(f'./plugins/{t["dir"]}','PLUGIN')
            file.init()
            client.sendFile(file)
            feedback=base64.b64decode(client.SOCKET.recv(1024)).decode(encoding='utf-8')
        file=File('./server_configs/plugin_parser.json','CONFIG')
        file.init()
        client.sendFile(file)
        return False
