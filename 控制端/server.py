import socket,threading,time,base64,json,os

mutex=threading.Lock()

#导入配置文件
with open('server_configs/command_parser.json', 'r', encoding='utf-8') as f:
    command_parser=json.load(f)
with open('server_configs/plugin_parser.json', 'r', encoding='utf-8') as f:
    plugin_parser=json.load(f)
with open('server_configs/config.json','r',encoding='utf-8') as f:
    config=json.load(f)

with open('server_configs/commands.py','r',encoding='utf-8') as f:
    t=f.read()
exec(t)
server_commands=ServerCommands()
client_commands=ClientCommands()

#创建ID函数
def createID():
    t=str(round(time.time()*1000))
    t=t[-16:]
    t=base64.b64encode(t.encode('utf-8')).decode('utf-8')
    return t

#解析命令
def parseCommand(command):
    t=command.split(' ',1)
    command=t[0]
    if not command in command_parser:
        print('未知命令！请使用help查看所有可用命令！')
        return False
    try:
        if len(t)>1:
            modifiers=t[1][:t[1].index('"')]
            modifiers=modifiers.split(' ')[:-1]
            args=t[1][t[1].index('"')+1:-1]
            args=args.split(' ',1)
        else:
            modifiers=[]
            args=[]
    except ValueError as err:
        print('命令格式有误！可能由于命令值得部分未加双引号引起！')
        return False
    res={'command':command,'modifiers':dict(),'args':args}
    jump_next=False
    for i in range(len(modifiers)):
        if jump_next:
            jump_next=False
            continue
        modifier=modifiers[i]
        if not modifier in command_parser[command]['modifiers']:
            print(f'命令格式有误！修饰符 {modifier} 不存在！')
            return False
        if command_parser[command]['modifiers'][modifier]['type']=='value':
            if modifiers[i+1][0]=='-':
                print(f'命令格式有误！修饰符 {modifier} 为传参型修饰符，未找到参数！')
                return False
            else:
                res['modifiers'][modifier]=modifiers[i+1]
                jump_next=True
        else:
            res['modifiers'][modifier]=True
    return res

#文件类
class File():
    def __init__(self,dir,file_type):
        self.dir=dir
        self.type=file_type
        self.size=0
        self.name=''
        self.ex=''
    #获取文件信息
    def init(self):
        t=os.path.basename(self.dir).split(".")
        self.name=''.join(t[0:-1])
        self.ex=t[-1]
        self.size=os.path.getsize(self.dir)

#客户端类
class Client():
    def __init__(self,SOCKET,id,addr,name):
        self.SOCKET=SOCKET
        self.CONNECTION_CHECK_SOCKET=None
        self.id=id
        self.addr=addr
        self.name=name
        self.cur_command=None
        self.cur_args=None
    #发送文件函数
    def sendFile(self,file):
        header={'type':file.type,'size':file.size,'name':file.name,'ex':file.ex}
        message=base64.b64encode(json.dumps(header).encode(encoding='utf-8'))
        self.SOCKET.sendall(message)
        feedback=base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8')

        send_size=0
        with open(file.dir,'rb') as f:
            while send_size<file.size:
                data=f.read((1024**2)*16)
                send_size+=len(data)
                self.SOCKET.sendall(data)
    #客户端的执行指令函数
    def runCommand(self):
        t={'command':self.cur_command,'args':self.cur_args}
        message=base64.b64encode(json.dumps(t).encode(encoding='utf-8'))
        self.SOCKET.sendall(message)

        try:
            do_return=eval(f'client_commands.{command_parser[self.cur_command]["func_name"]}')(self)
            if do_return:
                self.cur_command=None
                self.cur_args=None
                return
        except AttributeError as err:
            print(err)
            print('命令函数有误或未在配置文件中定义！')

        feedback=json.loads(base64.b64decode(self.SOCKET.recv(1024)).decode(encoding='utf-8'))
        if feedback['status']=='FAILED':
            print(f'{self.id}:执行失败！错误:{feedback["error"]}')
        self.cur_command=None
        self.cur_args=None

#服务器函数
class ControlServer():
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clients=[]
        self.cur_finished=0
        self.target_finished=0
    #服务端的处理命令函数
    def handleCommand(self,command):
        t=parseCommand(command)
        if not t:
            return
        command=t['command']
        modifiers=t['modifiers']
        args=t['args']

        try:
            do_return=eval(f'server_commands.{command_parser[command]["func_name"]}')(self)
            if do_return:
                return
        except AttributeError as err:
            print('命令函数有误或未在配置文件中定义！')
            return

        if '-t' in modifiers:
            mutex.acquire()
            self.target_finished=1
            mutex.release()
            targetID=modifiers['-t']
            for c in self.clients:
                if c.id==targetID:
                    c.cur_command=command
                    c.cur_args=args
                    break
        else:
            mutex.acquire()
            self.target_finished=len(self.clients)
            mutex.release()
            for c in self.clients:
                c.cur_command=command
                c.cur_args=args
        while self.cur_finished<self.target_finished:
            pass
        print('指令执行完成！')
        mutex.acquire()
        self.cur_finished=0
        self.target_finished=0
        mutex.release()
    #处理客户端请求函数
    def _start(self):
        client,addr=self.SOCKET.accept()
        threading.Thread(target=self._start).start()
        # print(addr)

        request=json.loads(base64.b64decode(client.recv(1024)).decode(encoding='utf-8'))
        if request['connection_type']=='MAIN_CLIENT':
            clientID=createID()
            t={'status':'Successfully Connected','id':clientID}
            client.sendall(base64.b64encode(json.dumps(t).encode(encoding='utf-8')))

            mutex.acquire()
            client=Client(client,clientID,addr,request['client_name'])
            self.clients.append(client)
            mutex.release()

            while not client.CONNECTION_CHECK_SOCKET:
                pass

            while True:
                if not client.cur_command:
                    continue

                client.runCommand()
                mutex.acquire()
                self.cur_finished+=1
                mutex.release()
        elif request['connection_type']=='CONNECTION_CHECK_SOCKET':
            for c in self.clients:
                if c.id==request['client_id']:
                    main_client=c
                    c.CONNECTION_CHECK_SOCKET=client
                    c.CONNECTION_CHECK_SOCKET.settimeout(3.0)
            while True:
                try:
                    message=base64.b64encode('Connection Check'.encode(encoding='utf-8'))
                    main_client.CONNECTION_CHECK_SOCKET.sendall(message)
                    feedback=base64.b64decode(main_client.CONNECTION_CHECK_SOCKET.recv(1024))\
                        .decode(encoding='utf-8')
                except Exception as err:
                    # print(err)
                    main_client.SOCKET.close()
                    main_client.CONNECTION_CHECK_SOCKET.close()
                    mutex.acquire()
                    self.clients.remove(main_client)
                    mutex.release()
                    return
    #启动服务器
    def run(self):
        self.SOCKET.bind((self.host,self.port))
        self.SOCKET.listen()
        threading.Thread(target=self._start).start()

if __name__ == '__main__':
    server=ControlServer(config['host'],config['port'])
    server.run()

    while True:
        command=input('输入要执行的指令\n>>:')
        server.handleCommand(command)
