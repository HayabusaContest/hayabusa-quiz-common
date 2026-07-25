# hayabusa-quiz-common

早押しクイズ AI 対戦システムの **共通リポジトリ** です。コンポーネント間の **プロトコル仕様([PROTOCOL.md](PROTOCOL.md))** と、開発時に全体をまとめて起動する **docker-compose** を提供します。システムの入口(全体像)も兼ねます。

## システム構成

| リポジトリ | 役割 |
| --- | --- |
| [hayabusa-quiz-server](https://github.com/HayabusaContest/hayabusa-quiz-server) | Go ゲームサーバ(lockstep配信・判定・採点・観戦フィード・常駐) |
| [hayabusa-quiz-agent](https://github.com/HayabusaContest/hayabusa-quiz-agent) | Python サンプルエージェント(LangChain 多プロバイダ) |
| [hayabusa-quiz-viewer](https://github.com/HayabusaContest/hayabusa-quiz-viewer) | 観戦ビューア(静的サイト) |
| **hayabusa-quiz-common**(このリポジトリ) | プロトコル仕様 + 開発用 docker-compose |

3コンポーネント(server / agent / viewer)は **WebSocket/JSON だけで連携**し、コードは共有しません。各コンポーネントの詳しい使い方はそれぞれの README を参照してください。

## プロトコル

サーバ→エージェントは JSON、エージェント→サーバは文字列1本。問題文を1文字ずつ配信し、各エージェントは `pass` か回答を返します(1問1回)。詳細は **[PROTOCOL.md](PROTOCOL.md)**。

## 開発用:docker compose で一括起動

**4リポジトリを同じ親ディレクトリに横並びで clone** した状態で、このリポジトリから:

```bash
cp .env.example .env          # 使うプロバイダの API キーを記入
docker compose up --build
```

- server `:8080` / agent×3 / 観戦ビューア **http://localhost:8081**。
- compose は `../hayabusa-quiz-server` 等の兄弟ディレクトリを参照します。
- 個別に起動したい場合は各リポジトリの README を参照してください。

## 対戦の2モード(server 設定)

- `reveal_all` … 最後まで開示し、各エージェントの最速正解位置でスコア。
- `first_answer` … 誰かが正解したら終了(誤答はロックアウトして続行)。

## 分離とコンテスト運用

- **開発**:4リポジトリを横並びに clone → compose で一括起動。
- **コンテスト**:同じコードのまま分離運用。
  - 大会サーバ … `hayabusa-quiz-server` を1ホストで常駐起動。
  - 参加者 … `hayabusa-quiz-agent` を各自動かし `SERVER_URL=ws://大会サーバ:8080/ws` で接続。
  - 観戦 … `hayabusa-quiz-viewer` を GitHub Pages 等に置き `?url=ws://大会サーバ:8080/viewer`。
- 連携はすべて WebSocket/JSON([PROTOCOL.md](PROTOCOL.md))のみ。
