import uvicorn
import asyncio
import pyodbc
import socket
import sys
import os
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List

# --- 0. 自動匯出邏輯 ---
def export_to_py():
    folder = r'C:\DW_API'
    file_path = os.path.join(folder, 'DW_API.py')
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # 取得當前執行儲存格的內容並寫入檔案
    try:
        # In[-1] 是目前正在執行的這個儲存格內容
        current_code = In[len(In)-1]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(current_code)
        print(f"✅ 檔案已同步匯出至: {file_path}")
    except Exception as e:
        print(f"匯出失敗: {e}")

# 執行匯出
export_to_py()

# --- 1. 初始化 API ---
app = FastAPI(
    title="BV DATA API",
    description="",
    version="1.2.1"
)

# SQL Server 連線設定
CONN_STR = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=winmssql01\bvhqlab01;'
    r'DATABASE=BV_DW;'
    r'Trusted_Connection=yes;'
    r'Timeout=30;' 
)

def execute_query(sql: str, params: tuple = ()):
    try:
        with pyodbc.connect(CONN_STR) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            if cursor.description is None:
                return []
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# --- 2. API 路徑 (Endpoint) ---
@app.get("/",tags=["status check"])
async def root():
    return {"status": "online"}

@app.get("/api/v1/inventory/all", tags=["Inventory"])
async def get_all_details():
    """獲取庫存表所有欄位資料 (不帶條件)"""
    sql = "SELECT * FROM [APL].[invertory_aging_dtl]"
    data = execute_query(sql)
    return {
        "status": "success",
        "count": len(data),
        "data": data
    }

@app.get("/api/v1/inventory/aging-report", tags=["Inventory Aging"])
async def get_aging_report(
    lot_no: Optional[List[str]] = Query(None, description="批號 (可重複輸入多個參數)"),
    item_desc: Optional[str] = Query(None, description="料號 (單一值查詢)")
):
    """獲取在庫天數分析報表"""
    base_sql = "SELECT * FROM [APL].[invertory_aging_dtl]"
    conditions = []
    all_params = []

    if lot_no:
        placeholders = ', '.join(['?'] * len(lot_no))
        conditions.append(f"[lot_no] IN ({placeholders})")
        all_params.extend(lot_no)
    
    if item_desc:
        conditions.append("[item_desc] = ?")
        all_params.append(item_desc)

    sql = base_sql
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    data = execute_query(sql, tuple(all_params))
    
    return {
        "status": "success",
        "filters_applied": {
            "lot_no": lot_no, 
            "item_desc": item_desc
        },
        "count": len(data),
        "data": data
    }

# --- 3. 啟動與環境檢查 ---
def get_local_ip():
    """取得本機區域網路 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

async def main():
    """非同步啟動主程式"""
    local_ip = get_local_ip()
    port = 8000
    print("-" * 50)
    print(f"BV DATA API 已啟動")
    print(f"Swagger UI: http://{local_ip}:{port}/docs")
    print("-" * 50)
  
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Jupyter 環境下通常會走到這裡
            task = loop.create_task(main())
        else:
            asyncio.run(main())
    except Exception as e:
        # 針對 Jupyter 已經有 running loop 的備案
        print(f"啟動提示: {e}")
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(main())