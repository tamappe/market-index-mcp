import os
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

def export():
    print("📊 Supabaseからデータ取得中...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 銘柄一覧取得
    symbols_res = supabase.table("symbols").select("*").execute()
    symbols = symbols_res.data
    print(f"銘柄数: {len(symbols)}")
    
    # 株価データ取得（ページネーション対応）
    all_data = []
    offset = 0
    limit = 10000
    
    while True:
        response = supabase.table("stock_daily") \
            .select("symbol,date,open,high,low,close,volume") \
            .order("symbol") \
            .order("date") \
            .range(offset, offset + limit - 1) \
            .execute()
        
        if not response.data:
            break
            
        all_data.extend(response.data)
        print(f"  取得中... {len(all_data)}件")
        
        if len(response.data) < limit:
            break
            
        offset += limit
    
    print(f"✅ 合計: {len(all_data)}件")
    
    # JSON出力
    output = {
        "symbols": symbols,
        "data": all_data
    }
    
    with open("market_data.json", "w") as f:
        json.dump(output, f)
    
    print("📁 market_data.json 出力完了")

if __name__ == "__main__":
    export()