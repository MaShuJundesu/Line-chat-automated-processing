import os
def load_config(file_path):
    config = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 跳過空行或註解行
            if line.strip() == '' or line.startswith('#'):
                continue
            # 分割鍵值對，並將它們加入字典  
            key, value = line.strip().split('*')
            config[key.strip()] = value.strip()
    return config
def hi(config,want):
    if want=="spreadsheet_url":
        return config.get('spreadsheet_url')
    elif want=="json_file_name":
        return config.get('json_file_name')
    elif want=="LineBotApi":
        return config.get('LineBotApi')
    elif want=="lineWebhookHandler":
        return config.get('lineWebhookHandler')
    elif want=="csvFile":
        return config.get('csvFile')
def take(want):
    config=load_config(os.path.join(os.path.dirname(__file__), '基本資料.txt'))
    want= hi(config,want)
    return want