# arena プロトコル

WebSocket 上で、**サーバ→エージェントは JSON**、**エージェント→サーバは文字列1本**でやり取りします(aiwolf-nlp 流)。エンドポイントは `ws://<host>:<port>/ws`。

## サーバ → エージェント(JSON)

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

## エージェント → サーバ(文字列)

- `NAME` への返信 … 自分の名前。
- `QUESTION_UPDATE` への返信 … `pass`(大文字小文字問わず)なら見過ごし。それ以外は**回答**とみなす。

## ルール(サーバ側)

- **lockstep**:各 `QUESTION_UPDATE` で、まだ回答権のある全エージェントの返信がそろってから次の1文字を配信。
- **1問1回**:`pass` 以外を返した時点でそのエージェントの回答は確定(以後その問題では配信されない)。誤答はその問題でロックアウト。
- **mode**(サーバ config):
  - `reveal_all` … 最後まで開示。各エージェントの最速正解位置でスコア。
  - `first_answer` … 誰かが正解したらその問題を終了(誤答者はロックアウトして続行)。
- **判定**:`normalized_match`(全半角・かな・記号などを正規化した上での文字列一致)。
- **得点**:正解が早いほど高い(`問題文長 − 正解位置 + 1`)。未正解=0。
