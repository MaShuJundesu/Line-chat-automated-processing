import re
import os
import gspread
import datareader
from google.oauth2.service_account import Credentials
from urllib3 import Retry
from datetime import datetime
#此程式為程式接往google 試算表的程式
# 授權並連接到 Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(os.path.join(os.path.dirname(__file__),datareader.take('json_file_name')))
client = gspread.authorize(creds)
sheet = client.open_by_key(datareader.take('spreadsheet_url')).sheet1
#print(datareader.take('spreadsheet_url'))
# 中文數字轉換對應表
zh2digit_table = {
    '零': 0, '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '百': 100, '千': 1000, '〇': 0, '○': 0, '○': 0, '０': 0, '１': 1, '２': 2, '３': 3, '４': 4, '５': 5, '６': 6, '７': 7, '８': 8, '９': 9, '壹': 1, '貳': 2, '參': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10, '佰': 100, '仟': 1000, '萬': 10000, '億': 100000000,'打':12
}

# 常見錯別字矯正對應表
item_corrections = {
    '鉛筆': ['鉛筆', '鉛皏', '鉛鄙'],
    '餅乾': ['餅乾', '餠乾', '餅干', '餅幹'],
    '燈泡': ['燈泡', '灯泡', '燈袍', '燈堡']
}

# 中文數字轉阿拉伯數字的函數，處理0到1億
def chinese_to_arabic(chinese_num):
    """將中文數字轉換為阿拉伯數字"""
    result = 0
    temp = 0  # 暫時存儲數字
    billion = 0  # 儲存 '億' 級的數字

    for char in chinese_num:
        num = zh2digit_table.get(char)
        if num is None:
            continue  # 跳過未識別的字符
        if num == 100000000:  # 億
            billion = (result + temp) * num
            result = 0
            temp = 0
        elif num == 10000:  # 萬
            result = (result + temp) * num
            temp = 0
        elif num >= 10 and num!=12:  # 十, 百, 千
            if temp == 0:
                temp = 1
            result += temp * num
            temp = 0
        elif num == 12:
            temp=result*12-10   
        else:
            temp = temp * 10 + num
    return result + temp + billion
# 中文數字轉換
def convert_chinese_to_arabic_extended(text):
    # 正則表達式匹配中文數字
    pattern = re.compile(r'([零一二兩三四五六七八九十百千萬億打]+)')
    matches = pattern.findall(text)
    

    # 將匹配到的中文數字替換為阿拉伯數字
    for match in matches:
        arabic_num = chinese_to_arabic(match)
        text = text.replace(match, str(arabic_num), 1)  # 確保一次只替換一個匹配到的數字
    return text

# 錯字矯正函數
def correct_typo(text):
    for correct_word, typo_list in item_corrections.items():
        for typo in typo_list:
            text = text.replace(typo, correct_word)
    return text


# 解析客戶留言 矯正文字及中文數字
def parse_message(message):
    # 中文數字轉換
    message = convert_chinese_to_arabic_extended(message)
    # 錯別字矯正
    message = correct_typo(message)
    return message
   
    
    
    

# 計算總和並將資料寫入 Google Sheet
def write_to_sheet(customer_name,uesr_id, parsed_items):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parsed_items=set_items(parsed_items)
    # 獲取下一個空行（從第三行開始）
    next_row = max(len(sheet.get_all_values()) + 1, 3)
    # 寫入客戶資料
    sheet.update_acell(f'A{next_row}', customer_name)
    sheet.update_acell(f'B{next_row}', uesr_id)
    sheet.update_acell(f'C{next_row}', parsed_items['餅乾'])
    sheet.update_acell(f'D{next_row}', f'=C{next_row}*D1')
    sheet.update_acell(f'E{next_row}', parsed_items['燈泡'])
    sheet.update_acell(f'F{next_row}', f"=E{next_row}*F1")
    sheet.update_acell(f'G{next_row}', parsed_items['鉛筆'])
    sheet.update_acell(f'H{next_row}', f"=G{next_row}*H1")
    sheet.update_acell(f'I{next_row}', f"=D{next_row}+F{next_row}+H{next_row}")
    sheet.update_acell(f'J{next_row}', current_time)


def set_items(parsed_items):
     # 定義產品和數量
    items = {'餅乾': 0, '燈泡': 0, '鉛筆': 0}

    # 定義每種物品的正則表達式模式
    patterns = [
        # 餅乾可以在數量之前或之後，允許使用 * 或 x，並允許不同的單位
        (r'(\d+)\s*(?:顆|盒|個)?\s*餅乾|餅乾\s*[*x]?\s*(\d+)', '餅乾'),
        (r'(\d+)\s*(?:顆|隻|個)?\s*燈泡|燈泡\s*[*x]?\s*(\d+)', '燈泡'),
        (r'(\d+)\s*(?:枝|支|隻|個)?\s*鉛筆|鉛筆\s*[*x]?\s*(\d+)', '鉛筆')
    ]

    # 匹配數量
    for pattern, item in patterns:
        match = re.search(pattern, parsed_items)
        if match:
            items[item] += int(match.group(1))  # 匹配的數字進行累加
    
    return items

# 主程式，處理訂單文字
def process_order(message):
    parsed_items = parse_message(message)
    result=set_items(parsed_items)
    result=format_output(result)
    return result

def texting(name):
    print(name)
    return name

def format_output(items):
    output = []
    for item, quantity in items.items():
        if quantity > 0:
            # 根據不同的產品名稱選擇單位
            unit = '個'
            output.append(f" {quantity}{unit}{item}")
    return ' '.join(output)

# 測試案例
customer_name = "客戶A"
uesr_id="test"
message = "100個餅乾1個鉛筆 101個燈泡 "
a=process_order(message)
print(a)
write_to_sheet(customer_name,uesr_id,a)