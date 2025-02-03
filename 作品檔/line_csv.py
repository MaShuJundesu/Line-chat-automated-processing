import csv
import os
import datareader
#此檔案為對內地csv紀錄客戶當前狀態的檔案
STATUS_FILE = os.path.join(os.path.dirname(__file__),datareader.take('csvFile'))

# 更新或新增客戶資料
def update_user_data(customer_name, product_info, status):
    file_exists = os.path.exists(STATUS_FILE)
    updated = False
    rows = []

    
    # 如果文件存在，先讀取現有的資料
    if file_exists:
        with open(STATUS_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # 讀取標題行
            rows.append(headers)    # 保留標題行
            for row in reader:
                # 如果找到對應的客戶名稱，更新該行數據
                if row[0] == customer_name:
                    row[1] = product_info
                    row[2] = status
                    updated = True
                rows.append(row)  # 保留每一行數據
    # 如果文件不存在或客戶不存在，則新增一行
    if not updated:
        if not file_exists:
            # 如果文件不存在，先加入標題行
            rows.append(['客戶名稱', '產品資訊', '確認當前狀態'])
        # 新增客戶資料
        rows.append([customer_name, product_info, status])
    
    
    
    # 將所有行（包括修改後的行）重新寫入CSV文件
    with open(STATUS_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)

# 讀取客戶資料
def read_user_data(customer_name):
    if not os.path.exists(STATUS_FILE):
        return None
    
    with open(STATUS_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳過標題行
        for row in reader:
            if row[0] == customer_name:
                return row
            
        update_user_data(customer_name,'未定東西',"new")
        with open(STATUS_FILE, newline='') as csvfile:
            for row in reader:
                if row[0] == customer_name:
                    return row
    return None

# 測試新客戶資料
#update_user_data('U4cd9452bcf3328336424f7bb243acd8d', '一個餅乾', 'pending')

# 測試讀取新客戶資料
#user_data = read_user_data('U4cd9452bcf3328336424f7bb243acd8d')
#print(user_data)  # ['Charlie', 'Product Y', 'pending']
