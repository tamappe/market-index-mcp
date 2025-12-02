import sqlite3
import os
from mcp.server.fastmcp import FastMCP

# DB自動生成
DB_PATH = os.path.join(os.path.dirname(__file__), "market_data.db")

if not os.path.exists(DB_PATH):
    print("📊 初回起動: データをダウンロード中...")
    from .setup_db import setup
    setup(DB_PATH)

# MCPサーバー作成
mcp = FastMCP("market-index")

def get_db():
    return sqlite3.connect(DB_PATH)

# ─────────────────────────────────────
# ツール定義
# ─────────────────────────────────────

@mcp.tool()
def list_symbols() -> list:
    """
    利用可能な銘柄一覧を取得
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, description FROM symbols")
    results = [
        {"symbol": row[0], "name": row[1], "description": row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return results

@mcp.tool()
def get_price_range(symbol: str, start_date: str, end_date: str) -> dict:
    """
    指定銘柄・期間の価格範囲を取得
    
    Args:
        symbol: 銘柄コード (例: ^GSPC, ^NDX)
        start_date: 開始日 (YYYY-MM-DD)
        end_date: 終了日 (YYYY-MM-DD)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 銘柄名取得
    cursor.execute("SELECT name FROM symbols WHERE symbol = ?", (symbol,))
    name_row = cursor.fetchone()
    name = name_row[0] if name_row else symbol
    
    # 統計取得
    cursor.execute("""
        SELECT 
            MIN(close), MAX(close), ROUND(AVG(close), 2), COUNT(*)
        FROM stock_daily
        WHERE symbol = ? AND date BETWEEN ? AND ?
    """, (symbol, start_date, end_date))
    
    row = cursor.fetchone()
    
    if not row or row[3] == 0:
        conn.close()
        return {"error": f"データなし: {symbol} ({start_date} ~ {end_date})"}
    
    # 最安値・最高値の日付
    cursor.execute("""
        SELECT date, close FROM stock_daily
        WHERE symbol = ? AND date BETWEEN ? AND ?
        ORDER BY close ASC LIMIT 1
    """, (symbol, start_date, end_date))
    min_day = cursor.fetchone()
    
    cursor.execute("""
        SELECT date, close FROM stock_daily
        WHERE symbol = ? AND date BETWEEN ? AND ?
        ORDER BY close DESC LIMIT 1
    """, (symbol, start_date, end_date))
    max_day = cursor.fetchone()
    
    conn.close()
    
    return {
        "symbol": symbol,
        "name": name,
        "period": f"{start_date} ~ {end_date}",
        "min_price": row[0],
        "min_date": min_day[0] if min_day else None,
        "max_price": row[1],
        "max_date": max_day[0] if max_day else None,
        "avg_price": row[2],
        "trading_days": row[3]
    }

@mcp.tool()
def get_price_on_date(symbol: str, date: str) -> dict:
    """
    特定日の価格データを取得
    
    Args:
        symbol: 銘柄コード
        date: 日付 (YYYY-MM-DD)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, date, open, high, low, close, volume
        FROM stock_daily WHERE symbol = ? AND date = ?
    """, (symbol, date))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": f"データなし: {symbol} on {date}"}
    
    return {
        "symbol": row[0],
        "date": row[1],
        "open": row[2],
        "high": row[3],
        "low": row[4],
        "close": row[5],
        "volume": row[6]
    }

@mcp.tool()
def compare_symbols(symbols: list, start_date: str, end_date: str) -> list:
    """
    複数銘柄を比較
    
    Args:
        symbols: 銘柄コードのリスト (例: ["^GSPC", "^NDX"])
        start_date: 開始日 (YYYY-MM-DD)
        end_date: 終了日 (YYYY-MM-DD)
    """
    results = []
    for symbol in symbols:
        data = get_price_range(symbol, start_date, end_date)
        if "error" not in data:
            # 期間リターン計算
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT close FROM stock_daily
                WHERE symbol = ? AND date >= ?
                ORDER BY date ASC LIMIT 1
            """, (symbol, start_date))
            start_price = cursor.fetchone()
            
            cursor.execute("""
                SELECT close FROM stock_daily
                WHERE symbol = ? AND date <= ?
                ORDER BY date DESC LIMIT 1
            """, (symbol, end_date))
            end_price = cursor.fetchone()
            
            conn.close()
            
            if start_price and end_price:
                return_pct = round(
                    (end_price[0] - start_price[0]) / start_price[0] * 100, 2
                )
                data["return_pct"] = return_pct
        
        results.append(data)
    
    return results

@mcp.tool()
def get_worst_days(symbol: str, year: int, limit: int = 5) -> list:
    """
    指定年の下落日ワーストランキング
    
    Args:
        symbol: 銘柄コード
        year: 年 (例: 2020)
        limit: 取得件数 (デフォルト5)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH daily_changes AS (
            SELECT 
                date,
                close,
                LAG(close) OVER (ORDER BY date) as prev_close
            FROM stock_daily
            WHERE symbol = ? AND date BETWEEN ? AND ?
        )
        SELECT 
            date,
            close,
            ROUND((close - prev_close) / prev_close * 100, 2) as change_pct
        FROM daily_changes
        WHERE prev_close IS NOT NULL
        ORDER BY change_pct ASC
        LIMIT ?
    """, (symbol, f"{year}-01-01", f"{year}-12-31", limit))
    
    results = [
        {"date": row[0], "close": row[1], "change_pct": row[2]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return results

@mcp.tool()
def get_best_days(symbol: str, year: int, limit: int = 5) -> list:
    """
    指定年の上昇日ベストランキング
    
    Args:
        symbol: 銘柄コード
        year: 年 (例: 2020)
        limit: 取得件数 (デフォルト5)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH daily_changes AS (
            SELECT 
                date,
                close,
                LAG(close) OVER (ORDER BY date) as prev_close
            FROM stock_daily
            WHERE symbol = ? AND date BETWEEN ? AND ?
        )
        SELECT 
            date,
            close,
            ROUND((close - prev_close) / prev_close * 100, 2) as change_pct
        FROM daily_changes
        WHERE prev_close IS NOT NULL
        ORDER BY change_pct DESC
        LIMIT ?
    """, (symbol, f"{year}-01-01", f"{year}-12-31", limit))
    
    results = [
        {"date": row[0], "close": row[1], "change_pct": row[2]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return results

@mcp.tool()
def get_yearly_summary(symbol: str, year: int) -> dict:
    """
    指定年の年間サマリー
    
    Args:
        symbol: 銘柄コード
        year: 年 (例: 2020)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # 年初・年末
    cursor.execute("""
        SELECT close FROM stock_daily
        WHERE symbol = ? AND date >= ?
        ORDER BY date ASC LIMIT 1
    """, (symbol, start_date))
    start_price = cursor.fetchone()
    
    cursor.execute("""
        SELECT close FROM stock_daily
        WHERE symbol = ? AND date <= ?
        ORDER BY date DESC LIMIT 1
    """, (symbol, end_date))
    end_price = cursor.fetchone()
    
    # 年間統計
    cursor.execute("""
        SELECT MIN(close), MAX(close), ROUND(AVG(close), 2), COUNT(*)
        FROM stock_daily
        WHERE symbol = ? AND date BETWEEN ? AND ?
    """, (symbol, start_date, end_date))
    stats = cursor.fetchone()
    
    conn.close()
    
    yearly_return = None
    if start_price and end_price:
        yearly_return = round(
            (end_price[0] - start_price[0]) / start_price[0] * 100, 2
        )
    
    return {
        "symbol": symbol,
        "year": year,
        "start_price": start_price[0] if start_price else None,
        "end_price": end_price[0] if end_price else None,
        "yearly_return_pct": yearly_return,
        "min_price": stats[0],
        "max_price": stats[1],
        "avg_price": stats[2],
        "trading_days": stats[3]
    }

def main():
    mcp.run()

if __name__ == "__main__":
    main()