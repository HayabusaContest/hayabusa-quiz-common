# hayabusa-quiz — 早押しクイズ AI 対戦システム

複数の LLM エージェントを WebSocket でサーバに接続し、問題文を1文字ずつ配信して早押しクイズを対戦させるシステムです。**コンポーネントごとに独立リポジトリ**で、連携は WebSocket/JSON のみ(コードは共有しません)。開発は docker compose で一括起動、コンテストでは各コンポーネントを分離デプロイできます。

エージェントは [hayabusa-chick](https://github.com/iggy157/hayabusa-chick) と同じ LangChain 多プロバイダの作りを流用しています。

## リポジトリ構成

| リポジトリ | 役割 |
| --- | --- |
| **hayabusa-quiz-server** | Go ゲームサーバ(接続ゲート・lockstep配信・判定・採点・観戦フィード・常駐) |
| **hayabusa-quiz-agent** | Python サンプルエージェント(LangChain 多プロバイダ、任意サーバに接続) |
| **hayabusa-quiz-viewer** | 観戦ビューア(独立した静的サイト) |
| **hayabusa-quiz-common** | プロトコル仕様([PROTOCOL.md](PROTOCOL.md))+ 開発用 docker-compose + この README |

3コンポーネント(server / agent / viewer)は**ネットワーク(WebSocket/JSON)だけで連携**します。プロトコルは [PROTOCOL.md](PROTOCOL.md)。

## 対戦の2モード(server の config)

- `reveal_all` … 問題を最後まで開示し、各エージェントの**最速正解位置でスコア**(全員データが取れる並列ベンチ寄り)。
- `first_answer` … **誰かが正解したらその問題を終了**(誤答者はロックアウトして続行)。競技寄り。

server の `config.yml` の `mode` で切り替え。**1問1回**(pass以外を返した時点で確定)。

## 動かし方 A:docker compose(一括起動)

**4リポジトリを同じ親ディレクトリに横並びで clone** した状態で、この common リポジトリから:

```bash
cp .env.example .env          # 使うプロバイダの API キーを記入
docker compose up --build
```

- server `:8080` / agent×3 / **観戦ビューア http://localhost:8081**。
- compose は `../hayabusa-quiz-server` 等の兄弟ディレクトリを参照します。
- server の `config.yml` の `agent_count`(既定3)と compose の agent 数を合わせてください。

## 動かし方 B:個別に起動(compose なし)

```bash
# 1) サーバ
cd ../hayabusa-quiz-server
go run .                      # ws://localhost:8080/ws で待受(3エージェント待ち)

# 2) エージェント(別ターミナルで人数分)
cd ../hayabusa-quiz-agent
uv sync
cp config/.env.example config/.env   # API キーを記入
AGENT_NAME=agent1 uv run python main.py
AGENT_NAME=agent2 uv run python main.py
AGENT_NAME=agent3 uv run python main.py
```

3体そろうとゲームが始まります。サーバは1ゲーム終了後も**常駐**し、次の3体が接続すれば新しいゲームを始めます。

## 観戦ビューア

`hayabusa-quiz-viewer` は**独立した静的サイト**(`index.html`、バニラJS・ビルド不要)で、`/viewer`(WebSocket, read-only)に繋いで対戦をライブ表示します(問題の逐次開示・各エージェントの回答◯✗・累計スコアボード)。

- **compose** … viewer サービスが配信。**http://localhost:8081**。
- **手元/コンテスト** … `index.html` を任意の静的ホスト(gh-pages 等)に置くか直接開く。接続先は `?url=ws://HOST:8080/viewer` で指定(既定は同ホストの 8080)。

サーバ自身は静的ファイルを配信しません(ゲームサーバに徹する)。

## 分離とコンテスト運用

- **今(開発)**:4リポジトリを横並びに clone → `docker compose up` で server / agent×N / viewer をまとめて起動。
- **将来(コンテスト)**:同じコードのまま分離運用。
  - **大会サーバ**:`hayabusa-quiz-server` を1ホストで常駐起動。
  - **参加者**:各自 `hayabusa-quiz-agent` を動かし、`SERVER_URL=ws://大会サーバ:8080/ws` で接続(モデル/プロンプトは自由)。
  - **観戦**:`hayabusa-quiz-viewer` を gh-pages 等に置き、`?url=ws://大会サーバ:8080/viewer` で観戦。
- 連携はすべて WebSocket/JSON([PROTOCOL.md](PROTOCOL.md))のみ。

## 今後

- 多チーム時の組み合わせ均一化(aiwolf の match_optimizer 相当)、複数ゲームのスケジューリング、認証(トークン)などは今後の拡張候補です。
