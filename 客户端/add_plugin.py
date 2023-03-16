import json

with open('./client_configs/plugin_parser.json', 'r', encoding='utf-8') as f:
    plugin_parser=json.load(f)

if __name__ == '__main__':
    plugin=input('输入插件名称，若没有则新创建：')
    description=input('输入插件解释：')
    plugin_dir=input('输入插件文件：')

    if not plugin in plugin_parser:
        plugin_parser[plugin]=dict()

    if description:
        plugin_parser[plugin]['description']=description
    if plugin_dir:
        plugin_parser[plugin]['dir']=plugin_dir

    with open('./client_configs/plugin_parser.json', 'w', encoding='utf-8') as f:
        json.dump(plugin_parser,f,indent=4,ensure_ascii=False)
