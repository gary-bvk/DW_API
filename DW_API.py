import os

# 1. 自動取得上一個 Cell 的內容 (In[-1] 代表上一個執行過的內容)
try:
    code_to_save = In[len(In)-2]  # 取得倒數第二個(即剛才那個) Cell 的內容
except:
    print("無法讀取上一個 Cell，請確認你剛才確實執行過該 Cell")
    code_to_save = ""

# 2. 設定目標路徑
folder = r'C:\DW_API'
file_path = os.path.join(folder, 'main.py')

# 3. 檢查並建立資料夾
if not os.path.exists(folder):
    os.makedirs(folder)

# 4. 執行寫入
if code_to_save:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code_to_save)
    print(f"✅ 成功！已將上一個 Cell 的程式碼匯出至: {file_path}")