# hayabusa-quiz-common

早押しクイズ AI 対戦システムの **共通リポジトリ** です。コンポーネント間の **プロトコルの正典**(machine-readable な [`protocol/protocol.json`](protocol/protocol.json) と人間向け [PROTOCOL.md](PROTOCOL.md))、3実装のズレを検知する **同期テスト**、開発時に全体をまとめて起動する **docker-compose** を提供します。システムの入口(全体像)も兼ねます。

## システム構成

| リポジトリ | 役割 |
| --- | --- |
| [hayabusa-quiz-server](https://github.com/HayabusaContest/hayabusa-quiz-server) | Go ゲームサーバ(lockstep配信・判定・採点・観戦フィード・常駐) |
| [hayabusa-quiz-agent](https://github.com/HayabusaContest/hayabusa-quiz-agent) | Python サンプルエージェント(LangChain 多プロバイダ) |
| [hayabusa-quiz-viewer](https://github.com/HayabusaContest/hayabusa-quiz-viewer) | 観戦ビューア(静的サイト) |
| **hayabusa-quiz-common**(このリポジトリ) | プロトコル仕様 + 開発用 docker-compose |

3コンポーネント(server / agent / viewer)は **WebSocket/JSON だけで連携**します。ランタイムのコード共有はしませんが、**プロトコルの契約(request 定数・フィールド・モード・得点式)は本リポジトリの [`protocol/protocol.json`](protocol/protocol.json) を正典**とし、各実装がそれに一致することをテストで担保します。各コンポーネントの詳しい使い方はそれぞれの README を参照してください。

## プロトコル(単一ソース + 同期テスト)

サーバ→エージェントは JSON、エージェント→サーバは文字列1本。問題文を1文字ずつ配信し、各エージェントは `pass` か回答を返します(1問1回)。

- **正典**:[`protocol/protocol.json`](protocol/protocol.json)(machine-readable)。人間向けは **[PROTOCOL.md](PROTOCOL.md)**。
- 各実装は自分の定数を持ちます:server=`protocol.go`、agent=`protocol.py`。
- **ズレ検知**:4リポジトリを横並びに clone した状態で、

  ```bash
  cd hayabusa-quiz-common
  python -m unittest discover -s tests    # protocol.json と server/agent の定数の一致を検査
  ```

  request/view/mode 定数・pass キーワード・protocol_version が食い違うと失敗します。プロトコルを変える時は protocol.json を更新し、両実装を追従させてください(互換破壊は semver を上げる)。

## 開発用:docker compose で一括起動

**4リポジトリを同じ親ディレクトリに横並びで clone** した状態で、このリポジトリから:

```bash
cp .env.example .env          # 使うプロバイダの API キーを記入
docker compose up --build
```

- server `:8080` / agent×3 / 観戦ビューア **http://localhost:8081**。
- compose は `../hayabusa-quiz-server` 等の兄弟ディレクトリを参照します。
- 個別に起動したい場合は各リポジトリの README を参照してください。

## 対戦の3モード(server 設定)

- `reveal_all` … 最後まで開示し、各エージェントの最速正解位置でスコア(1問1回・誤答ロックアウト)。
- `first_answer` … 誰かが正解したら終了(誤答はロックアウトして続行)。競技寄り。
- `benchmark` … 誤答ロックアウト無し・毎トークン回答可。常時回答型(pass無し)がそのまま乗る。

## 分離とコンテスト運用

- **開発**:4リポジトリを横並びに clone → compose で一括起動。
- **コンテスト**:同じコードのまま分離運用。
  - 大会サーバ … `hayabusa-quiz-server` を1ホストで常駐起動。
  - 参加者 … `hayabusa-quiz-agent` を各自動かし `SERVER_URL=ws://大会サーバ:8080/ws` で接続。
  - 観戦 … `hayabusa-quiz-viewer` を GitHub Pages 等に置き `?url=ws://大会サーバ:8080/viewer`。
- 連携はすべて WebSocket/JSON([PROTOCOL.md](PROTOCOL.md))のみ。
