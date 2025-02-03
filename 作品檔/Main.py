from turtle import st
from pyparsing import line_start
import detasetting
import line_csv
import datareader
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
app = Flask(__name__)

line_bot_api = LineBotApi(datareader.take('LineBotApi'))

# 設定LINE Webhook處理器
# 這裡需要填入你的Channel Secret 補充: 在 line bot 中的basic settings 選項中
handler = WebhookHandler(datareader.take('lineWebhookHandler'))

# 設定LINE Webhook的路由，用於接收LINE平台的回調請求
#下面內部的/callback 也需寫入line Developers的webhook 中 補充line 是傳資料到API的位置 若未在LINE Developers填寫會出現404 bug
@app.route("/callback", methods=['POST'])
def callback():
    # 從LINE請求頭中獲取簽名，這是為了確保請求的真實性
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # 將請求的內容和簽名交由WebhookHandler處理
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 如果簽名無效，返回400錯誤碼
        abort(400)

    # 如果處理成功，返回200 OK
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 從接收到的事件中提取用戶發送的文字
    user_text = event.message.text
    user_id = event.source.user_id
    user_message = event.message.text.strip().lower()
    
    try:
        profile = line_bot_api.get_profile(user_id)#取用戶資訊
        user_name = profile.display_name  # 用戶的名稱
        user_status = profile.status_message  # 用戶的狀態消息（可選）
    except Exception as e:
        user_name = "未知用戶"
        user_status = "無法取得用戶狀態"
    # 將提取到的文字丟給detasetting處理文字
    status = line_csv.read_user_data(user_id)
    date = line_csv.read_user_data(user_id)[1]
    
    
    if status[2] == "pending_confirmation":  # 如果用戶正在等待確認
        if user_message == "yes":
            line_csv.update_user_data(user_id,date, "confirmed")  # 更新狀態為已確認
            detasetting.write_to_sheet(user_name,user_id,date)
            # 回復用戶，告知訊息已成功保存到Google Sheets
            reply_message = f"感謝{user_name}的確認！您的訂單{date}已上傳雲端。"
        elif user_message == "no":
            line_csv.update_user_data(user_id,date,"cancelled")  # 更新狀態為取消
            reply_message = f"您的,{date}的訂單已取消。"
        else:
            reply_message = f"{user_name},訂單: {date}請回覆 'yes' 確認或 'no' 取消。"
    elif status[2] == "new":
        line_csv.update_user_data(user_id,"", "")  # 設置狀態為待確認
        reply_message = "新增資料中，請再次輸入"   
    else:
        # 如果不是等待確認的狀態，則詢問是否進行確認
        text=detasetting.process_order(user_text)
        if text=="":
            text="無接收到訂單資訊"
            reply_message = f"{text}請確認輸入內容"
        line_csv.update_user_data(user_id,text, "pending_confirmation")  # 設置狀態為待確認
        reply_message = f"{user_name},請問您要確認訂單 {text} 是否正確？請回覆 'yes' 或 'no'。"
        
    
    
    #text=detasetting.texting(user_name)
    
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=reply_message)
    )

# 函數：讀取客戶狀態

# 當收到訊息事件時，執行這個函數
# 啟動Flask應用
if __name__ == "__main__":
    # 設定應用運行的端口為5000
    app.run(port=5000)

