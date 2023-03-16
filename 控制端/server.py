import socket,threading,time,base64,json,os

mutex=threading.Lock()

with open('server_configs/command_parser.json', 'r', encoding='utf-8') as f:
    command_parser=json.load(f)
with open('server_configs/config.json','r',encoding='utf-8') as f:
    config=json.load(f)

def createID():
    t=str(round(time.time()*1000))
    t=t[-16:]
    t=base64.b64encode(t.encode('utf-8')).decode('utf-8')
    return t

class File():
    def __init__(self,dir,file_type):
        self.dir=dir
        self.type=file_type
        self.size=0
        self.name=''
        self.ex=''
    def init(self):
        t=os.path.basename(self.dir).split(".")
        self.name=''.join(t[0:-1])
        self.ex=t[-1]
        self.size=os.path.getsize(self.dir)

class ControlServer():
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clients=[]
        self.cur_command=None
        self.cur_args=[]
        self.cur_finished=0
        self.target_finished=0
    def sendFile(self,client,file):
        header={'type':file.type,'size':file.size,'name':file.name,'ex':file.ex}
        message=base64.b64encode(json.dumps(header).encode(encoding='utf-8'))
        client.sendall(message)

        send_size=0
        with open(file.dir,'rb') as f:
            while send_size<file.size:
                data=f.read((1024**2)*16)
                send_size+=len(data)
                client.sendall(data)
                print(send_size)
    def handleCommand(self,command):
        try:
            command,args=command.split(' ',1)
        except:
            args=''
        args=args.split(' ')
        if command=='help':
            print('------------------------------------')
            for c,t in command_parser.items():
                print(f'{c}:\n    {t["description"]}')
            print('------------------------------------')
            return
        elif command=='connectionInfo':
            if len(self.clients)<=0:
                print('当前并无连接...')
            else:
                print('------------------------------------')
                for c in self.clients:
                    print(f'ID: {c["id"]},名称: {c["name"]}')
                print('------------------------------------')
            return
        mutex.acquire()
        self.cur_command=command
        self.cur_args=args
        mutex.release()
        while self.cur_finished<len(self.clients):
            pass
        print('指令执行完成！')
        mutex.acquire()
        self.cur_command=None
        self.cur_args=[]
        self.cur_finished=0
        mutex.release()
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
            self.clients.append({'SOCKET':client,'id':clientID,'name':request['client_name']})
            mutex.release()

            while True:
                if not self.cur_command:
                    continue

                t={'command':self.cur_command,'args':self.cur_args}
                message=base64.b64encode(json.dumps(t).encode(encoding='utf-8'))
                client.sendall(message)
                if self.cur_command=='sendPlugin':
                    if self.cur_args:
                        file=File(self.cur_args[0],'PLUGIN')
                        file.init()
                        if len(self.cur_args)>1 and self.cur_args[self.cur_args.index('-t')+1]==clientID\
                                or len(self.cur_args)==1:
                            self.sendFile(client,file)

                feedback=json.loads(base64.b64decode(client.recv(1024)).decode(encoding='utf-8'))
                if feedback['status']=='FAILED':
                    print(f'{clientID}:执行失败！错误:{feedback["error"]}')
                mutex.acquire()
                self.cur_finished+=1
                mutex.release()
                while self.cur_finished<len(self.clients):
                    pass
                time.sleep(0.2)
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
