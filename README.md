# Market Index MCP

S&P500、NASDAQ100、日経225などの市場指標データを自然言語で検索できるMCPサーバー

## 特徴

-  **約100年分の市場データ**（77,870件）を即座に検索
-  **Claude Desktop と統合** - 自然言語で質問するだけ
-  **初回起動時に自動セットアップ** - 設定不要
-  **ローカルキャッシュ** - 高速クエリ（2-15ms）

## 対応銘柄

| シンボル | 名称 | データ期間 |
|----------|------|-----------|
| ^GSPC | S&P 500 | 1927年〜 |
| ^NDX | NASDAQ 100 | 1985年〜 |
| ^DJI | Dow Jones | 1992年〜 |
| ^N225 | Nikkei 225 | 1965年〜 |
| ^FTSE | FTSE 100 | 1984年〜 |
| ^VIX | VIX (恐怖指数) | 1990年〜 |

## インストール

### 前提条件

- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/) または pip
- Claude Desktop

### Claude Desktop 設定

1. **uvx のパスを確認**

```bash
which uvx
# 例: /opt/homebrew/bin/uvx
```

2. **設定ファイルを編集**

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "market-index": {
      "command": "/opt/homebrew/bin/uvx",
      "args": [
        "--from", "git+https://github.com/tamappe/market-index-mcp.git",
        "market-index-mcp"
      ]
    }
  }
}
```

> **重要**: `command` には `uvx` のフルパスを指定してください。相対パス `"uvx"` だと Claude Desktop から見つからない場合があります。

3. **Claude Desktop を再起動**

初回起動時にデータを自動ダウンロード（約10MB、30秒程度）します。

### 手動インストール（開発用）

```bash
git clone https://github.com/tamappe/market-index-mcp.git
cd market-index-mcp
pip install -e .

# 実行
market-index-mcp
```

## 使用例

Claude Desktop で以下のような質問ができます：

- 「S&P500の2020年3月の最安値と最高値を教えて」
- 「2020年のS&P500とNASDAQ100を比較して」
- 「2008年のダウ平均ワースト下落日トップ5は？」
- 「日経225の2023年の年間リターンは？」
- 「コロナショック時のVIXはどこまで上がった？」

## 提供ツール

| ツール名 | 説明 |
|---------|------|
| `list_symbols` | 利用可能な銘柄一覧を取得 |
| `get_price_range` | 指定期間の価格範囲（最高値・最安値・平均）を取得 |
| `get_price_on_date` | 特定日の価格データを取得 |
| `compare_symbols` | 複数銘柄のパフォーマンスを比較 |
| `get_worst_days` | 指定年の下落日ワーストランキング |
| `get_best_days` | 指定年の上昇日ベストランキング |
| `get_yearly_summary` | 年間サマリー（年初来リターンなど） |

## トラブルシューティング

### サーバーが起動しない（Server disconnected）

**1. ログを確認**

```bash
cat ~/Library/Logs/Claude/mcp-server-market-index.log | tail -50
```

**2. uvx のパスを確認**

```bash
which uvx
```

設定ファイルの `command` にフルパスを指定しているか確認してください。

### SSL証明書エラー

エラーメッセージ:
```
ssl.SSLCertVerificationError: certificate verify failed
```

**解決方法:**

```bash
# Python 3.12 の場合
sudo /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m pip install --upgrade certifi

# または Install Certificates コマンドを実行
/Applications/Python\ 3.12/Install\ Certificates.command
```

### "Unexpected token" エラー

エラーメッセージ:
```
MCP market-index: Unexpected token '📊', "📊 初回起動: デ"... is not valid JSON
```

これは古いバージョンの問題です。最新版では修正済みです。

**解決方法:**

```bash
# uvx キャッシュをクリア
rm -rf ~/.cache/uv/archive-v0/

# Claude Desktop を再起動
```

### データダウンロードに失敗する

GitHub Releases からデータを取得できない場合：

1. ネットワーク接続を確認
2. https://github.com/tamappe/market-index-mcp/releases にアクセスできるか確認
3. プロキシ環境の場合は環境変数を設定

### キャッシュを完全にクリアしたい

```bash
# uvx キャッシュ
rm -rf ~/.cache/uv/

# Claude Desktop を再起動
```

## 技術詳細

### アーキテクチャ

```
Database (データ管理)
    ↓ GitHub Actions (平日9時自動更新)
GitHub Releases (market_data.json)
    ↓ 初回起動時にダウンロード
SQLite (ローカルキャッシュ)
    ↓
MCP Server → Claude Desktop
```

### データ更新

- GitHub Actions で平日 JST 9:00 に自動更新
- Supabase から最新データを取得し、GitHub Releases に反映
- MCPサーバー再起動時に自動で最新版を取得


## ライセンス

MIT
