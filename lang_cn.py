﻿table = {
'Add Device': '添加设备',
'Remove Device': '删除设备',
'Bluetooth':'蓝牙',
'---Paired Devices---':'已配对设备',
'Device is removed.':'设备已删除',
'Scanning':'正在扫描',
'Please wait...':'请稍候',
'Devices Found':'扫描到的设备',
'Pairing...':'正在配对',
'Device is paired.':'设备成功配对',
'Failed to pair device.':'设备配对失败',
'Connecting bluetooth audio device...': '正在尝试连接蓝牙音频设备',
'Failed to connect bluetooth audio device.\nFallback to 3.5mm output.': '连接蓝牙音频设备失败，\n将会从3.5mm接口输出音频。',
'Internal Storage': '内置存储',
'UDisk':'U盘',
'Select Device':'选择设备',
'Wireless Casting':'无线投屏',
'Waiting...\nhttp://%s':'等待手机投屏中...\nhttp://%s',
'Format':'格式化',
'Done':'完成',
'Format cancelled.':'格式化已取消',
'System Info':'系统信息',
'Network Info': '网络信息',
'WiFi SSID': '输入WiFi名称',
'WiFi Password': '输入WiFi密码',
'WiFi config cancelled.': 'WiFi配置已取消',
'WiFi config cleared.': 'WiFi配置已清除',
'WiFi config saved.': 'WiFi配置已保存',
'Video Player': '视频播放选项',
'WiFi': 'WiFi配置',
'Software Update': '软件更新',
'<!> Format Internal Storage': '<!> 格式化内置存储',
'Enter "OK" to DELETE ALL DATA.':'<!> 要确认格式化，请输入OK',
'Settings': '设置',
'Default Volume: %d dB': '默认音频音量: %d dB',
'Default Video Delay: %d' : '默认视频延迟: %d',
'Default Video Delay for Bluetooth: %d': '默认视频延迟（蓝牙连接时）: %d',
'Shutdown': '关机',
'Power options': '电源选项',
'Software Update': '软件更新',
'Checking update...': '正在检查软件更新',
'Check update failed.': '连接更新服务器失败',
'Your software is up to date.': '你的软件已是最新版。',
'>Update Later': '>暂不更新',
'>Update Now': '>立即更新',
'New version: ': '新版本: ',
'Software update is available.': '有新版本可供更新',
'Downloading update package(%d KiB)...': '下载更新中(%d KiB)',
'Update package verification failed.': '更新包验证失败',
'Files':'文件浏览',
'Projector Control': '投影控制',
'Main': '主菜单',
'Standby': '待机',
}

def TR(word):
    if isinstance(word, unicode):
        return word 
    if table.has_key(word):
        return table[word].decode('utf-8')
    return word.decode('utf-8')