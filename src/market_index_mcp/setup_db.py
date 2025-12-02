import sqlite3
import urllib.request
import json
import os

DATA_URL = "https://github.com/{owner}/{repo}/releases/download/data-latest/market_data.json"

def get_data_url():
    # 環境変数またはデフォルト値
    owner = os.environ.get("MCP_REPO_OWNER", "YOUR_GITHUB_USERNAME")
    repo = os.environ.get("MCP_REPO_NAME", "market-index-mcp")
    return DATA_URL.format(owner=owner, repo=repo)

def setup(db_path="market_data.db"):
    print("📊 市場データをダウンロード中...")
    
    url = get_data_url()
    
    try:
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read())
    except Exception as e:
        print(f"❌ ダウンロード失敗: {e}")
        print(f"   URL: {url}")
        raise
    
    symbols = data["symbols"]
    stock_data = data["data"]
    
    print(f"  銘柄数: {len(symbols)}")
    print(f"  データ件数: {len(stock_data)}")
    
    # SQLite作成
    conn = sqlite3.connect(db_path)
    
    # テーブル作成
    conn.execute("""
        CREATE TABLE IF NOT EXISTS symbols (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (symbol, date)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON stock_daily(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON stock_daily(date)")
    
    # データ挿入
    for s in symbols:
        conn.execute(
            "INSERT OR REPLACE INTO symbols VALUES (?, ?, ?)",
            (s["symbol"], s["name"], s.get("description"))
        )
    
    for row in stock_data:
        conn.execute(
            "INSERT OR REPLACE INTO stock_daily VALUES (?, ?, ?, ?, ?, ?, ?)",
            (row["symbol"], row["date"], row["open"], row["high"],
             row["low"], row["close"], row["volume"])
        )
    
    conn.commit()
    conn.close()
    
    print("✅ market_data.db 作成完了！")

if __name__ == "__main__":
    setup()