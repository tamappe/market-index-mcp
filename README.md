# Market Index MCP

S&P500、NASDAQ100、日経225などの市場指標データを自然言語で検索できるMCPサーバー

## 対応銘柄

| シンボル | 名称 |
|----------|------|
| ^GSPC | S&P 500 |
| ^NDX | NASDAQ 100 |
| ^DJI | Dow Jones |
| ^N225 | Nikkei 225 |
| ^FTSE | FTSE 100 |
| ^VIX | VIX (恐怖指数) |

## インストール

### Claude Desktop設定

`claude_desktop_config.json` に追加:
```json
{
  "mcpServers": {
    "market-index": {
      "command": "uvx",
      "args": ["market-index-mcp"],
      "env": {
        "MCP_REPO_OWNER": "tamappe",
        "MCP_REPO_NAME": "market-index-mcp"
      }
    }
  }
}
```

### 手動インストール
```bash
git clone https://github.com/tamappe/market-index-mcp.git
cd market-index-mcp
pip install -e .
```

## 使用例

- 「S&P500の2020年3月の最安値と最高値を教えて」
- 「2020年のS&P500とNASDAQ100を比較して」
- 「2008年のダウ平均ワースト下落日トップ5は？」
- 「日経225の2023年の年間リターンは？」

## ライセンス

MIT