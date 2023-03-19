import json

with open('server_configs/command_parser.json', 'r', encoding='utf-8') as f:
    command_parser=json.load(f)

if __name__ == '__main__':
    command=input('输入指令名称，若没有则新创建：')
    description=input('输入指令解释：')
    func_name=input('输入对应函数名称：')
    modifiers=input('输入这个指令需要的修饰参数，逗号分隔\n格式：参数名称 类型(value,modify) 解释\n>>:').split(',')

    if not command in command_parser:
        command_parser[command]=dict()

    if description:
        command_parser[command]['description']=description
    if func_name:
        command_parser[command]['func_name']=func_name
    if modifiers[0]:
        command_parser[command]['modifiers']=dict()
        for t in modifiers:
            if not t:
                break
            t=t.split(' ')
            command_parser[command]['modifiers'][t[0]]={'type':t[1],
                                                   'description':t[2]}

    with open('server_configs/command_parser.json', 'w', encoding='utf-8') as f:
        json.dump(command_parser,f,indent=4,ensure_ascii=False)
