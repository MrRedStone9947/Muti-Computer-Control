import win32api,win32con,sys,os

file_name=input('输入客户端文件名：')
name='remote_control_client'
if hasattr(sys, 'frozen'):
    path=os.path.dirname(sys.executable)
else:
    path=os.path.dirname(__file__)
path=path+f'\{file_name}'
print(path)
KeyName='Software\Microsoft\Windows\CurrentVersion\Run'
key=win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE,KeyName,0,win32con.KEY_ALL_ACCESS)
win32api.RegSetValueEx(key,name,0,win32con.REG_SZ,path)
win32api.RegCloseKey(key)

input('执行完成！按任意键退出...')
