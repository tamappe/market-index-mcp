import sqlite3
import urllib.request
import ssl
import json
import os
import sys

DATA_URL = "https://github.com/{owner}/{repo}/releases/download/data-latest/market_data.json"

def log(msg):
    """ログ出力（stderr経由でMCPと干渉しない）"""
    print(msg, file=sys.stderr)

def get_data_url():
    owner = os.environ.get("MCP_REPO_OWNER", "tamappe")
    repo = os.environ.get("MCP_REPO_NAME", "market-index-mcp")
    return DATA_URL.format(owner=owner, repo=repo)

def get_ssl_context():
    """SSL コンテキストを取得（certifi があれば使用）"""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        # certifi がない場合はデフォルトコンテキスト
        return ssl.create_default_context()

def setup(db_path="market_data.db"):
    log("📊 市場データをダウンロード中...")
    
    url = get_data_url()
    
    try:
        ctx = get_ssl_context()
        with urllib.request.urlopen(url, context=ctx) as res:
            data = json.loads(res.read())
    except Exception as e:
        log(f"❌ ダウンロード失敗: {e}")
        log(f"   URL: {url}")
        raise
    
    symbols = data["symbols"]
    stock_data = data["data"]
    
    log(f"  銘柄数: {len(symbols)}")
    log(f"  データ件数: {len(stock_data)}")
    
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
    
    log("✅ market_data.db 作成完了！")

if __name__ == "__main__":
    setup()
