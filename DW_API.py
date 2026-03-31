#!/usr/bin/env python
# coding: utf-8

# In[1]:


import uvicorn
import asyncio
import pyodbc
import socket
import sys
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List

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
        # 使用 with 確保連線會自動關閉
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
    print(f"http://{local_ip}:{port}/docs")
    print("-" * 50)
  

    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        # 檢查是否已有運行的事件迴圈 (預防在某些互動式環境下執行)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已經在跑了，就直接把任務塞進去
            task = loop.create_task(main())
        else:
            # 標準 .py 執行模式
            asyncio.run(main())
    except RuntimeError:
        # 萬一 asyncio.run 失敗的備用方案
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAPI 服務已由使用者關閉")


# In[ ]:





# In[ ]:




