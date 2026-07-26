# hayabusa プロトコル (v1.0.0)

WebSocket 上で、**サーバ→エージェントは JSON**、**エージェント→サーバは文字列1本**でやり取りします(aiwolf-nlp 流)。観戦ビューアには別途 **観戦イベント(JSON)** を配信します。

- エージェント接続:`ws://<host>:<port>/ws`
- 観戦接続(read-only):`ws://<host>:<port>/viewer`

> **正典は [`protocol/protocol.json`](protocol/protocol.json)**(machine-readable)。この Markdown はそれを人間向けに記述したものです。server(Go)`protocol.go` / agent(Python)`protocol.py` / viewer は各自の定数を持ちますが、[`tests/test_protocol_sync.py`](tests/test_protocol_sync.py) が protocol.json と一致するかを検査します(3者のズレ検知)。

## 1. サーバ → エージェント(JSON)

`request` が種別。付随フィールドは種別により異なります。

| request | フィールド | 意味 | 返信 |
| --- | --- | --- | --- |
| `NAME` | — | 接続直後の名乗り要求 | **必要**:エージェント名(文字列) |
| `QUESTION_START` | `question_id` | 新しい問題の開始(状態リセット) | 不要 |
| `QUESTION_UPDATE` | `question_id`, `cursor`, `text` | 問題文が1文字進んだ(`text`=ここまでの断片) | **必要**:`pass` か 回答(文字列) |
| `RESULT` | `question_id`, `answer`, `scores` | その問題の正解と各自の得点 | 不要 |
| `FINISH` | `scores` | 全問終了・最終スコア | 不要(切断) |

例:
```json
{"request":"NAME"}
{"request":"QUESTION_START","question_id":1}
{"request":"QUESTION_UPDATE","question_id":1,"cursor":5,"text":"日本で一番"}
{"request":"RESULT","question_id":1,"answer":"北岳","scores":{"agent1":12,"agent2":0}}
{"request":"FINISH","scores":{"agent1":30,"agent2":8}}
```

## 2. エージェント → サーバ(文字列)

- `NAME` への返信 … 自分の名前。
- `QUESTION_UPDATE` への返信 … `pass`(大文字小文字問わず)なら見過ごし。それ以外は**回答**とみなす。

## 3. サーバ → 観戦ビューア(JSON, read-only)

`/viewer` に流れる観戦イベント。`type` が種別。ビューアはこれを畳み込んで盤面を描画し、そのままログ(JSONL)にも保存されます(アーカイブ再生に使用)。

| type | フィールド | 意味 |
| --- | --- | --- |
| `game_start` | `agents` | 参加エージェント名の一覧 |
| `question_start` | `question_id`, `total` | 問題開始(`total`=問題文の総文字数) |
| `reveal` | `question_id`, `cursor`, `text` | 1文字開示(`text`=ここまでの断片) |
| `answer` | `question_id`, `cursor`, `agent`, `reply`, `correct` | あるエージェントの回答(◯/✗) |
| `result` | `question_id`, `text`, `answer`, `scores`, `totals` | 問題終了。`text`=問題文全文、`scores`=この問の得点、`totals`=累計 |
| `finish` | `scores` | 最終スコア |

## 4. ルール(サーバ側)

- **lockstep**:各 `QUESTION_UPDATE` で、まだ回答権のある全エージェントの返信がそろってから次の1文字を配信。
- **1問1回**:`pass` 以外を返した時点でそのエージェントの回答は確定(以後その問題では配信されない)。誤答はその問題でロックアウト。
- **mode**(サーバ config):
  - `reveal_all` … 最後まで開示。各エージェントの最速正解位置でスコア。
  - `first_answer` … 誰かが正解したらその問題を終了(誤答者はロックアウトして続行)。
  - `benchmark` … 誤答ロックアウト無し・毎トークン回答可。常時回答型(`pass` 無し)がそのまま乗る。
- **判定**:`normalized_match`(全半角・かな・記号などを正規化した上での部分文字列一致)。
- **得点**:正解が早いほど高い(`問題文長 − 正解位置 + 1`)。未正解=0。

## 5. バージョニング

`protocol_version`(現在 `1.0.0`)は protocol.json / 各実装の定数に埋め込まれています。互換性を壊す変更(フィールド増減・意味変更)を行う場合は semver を上げ、sync テストで全実装を追従させてください。
