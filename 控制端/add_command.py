import json

with open('server_configs/command_parser.json', 'r', encoding='utf-8') as f:
    command_parser=json.load(f)

if __name__ == '__main__':
    command=input('输入指令名称，若没有则新创建：')
    description=input('输入指令解释：')

    if not command in command_parser:
        command_parser[command]=dict()

    if description:
        command_parser[command]['description']=description

    with open('server_configs/command_parser.json', 'w', encoding='utf-8') as f:
        json.dump(command_parser,f,indent=4,ensure_ascii=False)
