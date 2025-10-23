# チャット調整機能の根本的問題分析

**作成日**: 2025-10-23
**報告者**: Claude Code
**目的**: チャット調整機能における表示不一致の根本原因を特定し、解決方針を提案する

---

## 📋 問題の概要

### 現象
ユーザーが「Please make the admin dashboard simple and affordable.」と入力したところ、以下の不一致が発生：

**期待される動作**:
- Admin Dashboardのみが調整される
- 他の成果物は変更されない、または最小限の変更

**実際の動作**:
- **全ての成果物が調整されている**
- Admin Dashboard以外も大幅に変更されている（例: Requirements Document、Basic Design等）

---

## 🔍 詳細な現象

### ユーザー入力
```
Please make the admin dashboard simple and affordable.
```

### システムからのメッセージ
```
Request received. Applying the following adjustments.

To simplify and make the admin dashboard more affordable,
I have adjusted the estimates to align with a unit cost of $500 per person-day.
This includes a reduction in person-days while maintaining the essential components
of each deliverable.

Subtotal: 93,500$ / Tax: 0$ / Total: 93,500$
```

### 実際の変更結果（Deliverable Details）

| 成果物 | 元の工数 | 調整後の工数 | 減少分 | 元の金額 | 調整後の金額 | 減少分 |
|--------|----------|--------------|--------|----------|--------------|--------|
| Requirements Document | 15.0 | 10.0 | -5.0 | $7,500 | $5,000 | -$2,500 |
| Basic Design Document | 15.0 | 12.0 | -3.0 | $7,500 | $6,000 | -$1,500 |
| Detailed Design Document | 15.0 | 12.0 | -3.0 | $7,500 | $6,000 | -$1,500 |
| Database Design | 12.5 | 10.0 | -2.5 | $6,250 | $5,000 | -$1,250 |
| API Design | 20.0 | 15.0 | -5.0 | $10,000 | $7,500 | -$2,500 |
| Frontend Development | 30.0 | 25.0 | -5.0 | $15,000 | $12,500 | -$2,500 |
| Backend Development | 30.0 | 25.0 | -5.0 | $15,000 | $12,500 | -$2,500 |
| Authentication Feature | 20.0 | 15.0 | -5.0 | $10,000 | $7,500 | -$2,500 |
| **Admin Dashboard** | **20.0** | **12.0** | **-8.0** | **$10,000** | **$6,000** | **-$4,000** |
| Unit Testing | 15.0 | 12.0 | -3.0 | $7,500 | $6,000 | -$1,500 |
| Integration Testing | 20.0 | 15.0 | -5.0 | $10,000 | $7,500 | -$2,500 |
| Operations Manual | 15.0 | 12.0 | -3.0 | $7,500 | $6,000 | -$1,500 |
| Deployment | 15.0 | 12.0 | -3.0 | $7,500 | $6,000 | -$1,500 |

**観察**:
- Admin Dashboardだけでなく、**13項目すべて**が調整されている
- Admin Dashboardの減少分は-8.0人日（最大）だが、他も-2.5〜-5.0人日減少している
- これはユーザーのリクエスト「Admin Dashboardを簡素化・安価にする」と一致しない

---

## 🧩 システムアーキテクチャの理解

### チャット調整機能の処理フロー

```
[ユーザー入力]
    ↓
[Backend API: /tasks/{task_id}/chat]
    ↓
[ChatService.process()]
    ↓
┌─────────────────────────────────────────┐
│ 1. ルールベース調整                      │
│    (_analyze_and_apply)                 │
│    - メッセージ解析                      │
│    - キーワード検出                      │
│    - ターゲット項目の特定                │
│    - 調整率の推定                        │
│    - 見積データ更新 → updated           │
│    - メッセージ生成 → rule_note         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. AI調整（オプション）                  │
│    - OpenAI API呼び出し                 │
│    - AI提案の取得                       │
│    - 見積データ上書き → updated (norm)  │
│    - メッセージ生成 → ai_note           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. 最終メッセージ生成                    │
│    - note = ai_note (if ai_adjusted)    │
│    - totals計算                         │
│    - suggestions生成                    │
└─────────────────────────────────────────┘
    ↓
[レスポンス返却]
    ↓
[フロントエンド表示]
```

### 関連コードファイル

1. **backend/app/services/chat_service.py**
   - `ChatService.process()` (767行目〜)
   - `_analyze_and_apply()` (177行目〜)
   - `_fit_budget()` (85行目〜)
   - `_unit_cost_change()` (119行目〜)
   - `_risk_buffer()` (139行目〜)
   - `_scope_reduce()` (161行目〜)

2. **backend/app/prompts/chat_prompts.py**
   - `get_proposal_generation_prompt()` (14行目〜)
   - AI調整用のプロンプト生成

3. **backend/app/api/v1/tasks.py**
   - `/tasks/{task_id}/chat` エンドポイント (383行目〜)

4. **backend/app/static/index.html**
   - `updateEstimatesView()` (973行目〜)
   - Deliverable Detailsの表示処理

---

## 🔬 根本原因の仮説

### 仮説1: ルールベース調整が全項目を対象にしている

**疑問点**:
- `_analyze_and_apply()`のターゲット検出ロジックが正しく動作していない
- 「admin dashboard」というキーワードを検出できていない
- `apply_to_all`フラグが誤ってTrueになっている

**確認すべきコード** (chat_service.py:177-350):
```python
def _analyze_and_apply(self, estimates, message):
    # メッセージ正規化
    m = message.lower()

    # ターゲット検出
    targets = []
    mapping = {
        '管理画面': ['管理', '管理画面', 'admin', ...],
        ...
    }

    # 全体適用フラグ
    apply_to_all = any(x in m for x in ['全体', '合計', ...])

    # 変更率の推定
    reduce_ratio = ...

    # 見積更新
    for e in estimates:
        match = apply_to_all or (any(t in name for t in targets))
        if match:
            # 調整を適用
```

**問題の可能性**:
1. `targets`が空のまま処理されている
2. `apply_to_all`が誤ってTrueになっている
3. キーワードマッピングに「admin」が含まれていない、または正しくマッチしていない

### 仮説2: AI調整が全項目を調整している

**疑問点**:
- AI（OpenAI API）に渡すプロンプトが不適切
- AIが「admin dashboard以外も調整すべき」と判断している
- AIからのレスポンスが全項目を含んでいる

**確認すべきコード** (chat_service.py:950-1044):
```python
prompt = {
    "role": "user",
    "content": (
        f"{language_instruction}\n\n"
        "以下は現在の見積です。各項目の人日(person_days)と金額(amount)を単価"
        f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
        ...
        "依頼文:\n" + (message or "") + "\n\n"
        "現在の見積(JSON):\n" + json.dumps(updated, ensure_ascii=False)
    ),
}
```

**問題の可能性**:
1. プロンプトに「Admin Dashboardのみを調整せよ」という指示が含まれていない
2. AIが「単価を$500に合わせる」という指示を「全体を調整する」と解釈している
3. AI調整が`updated = norm`で全項目を上書きしている

### 仮説3: フロントエンド表示の問題

**疑問点**:
- バックエンドからは正しいデータが返ってきているが、フロントエンドで誤った値を表示している
- 変更差分（-5.0など）の計算が誤っている

**確認すべきコード** (index.html:973-1069):
```javascript
function updateEstimatesView(apiData, fromChat=false) {
    const ests = apiData.estimates;
    const prev = (window.prevEstimates || window.lastEstimates || []);

    // 差分計算
    const prevItem = prevMap.get(name);
    let deltaPd = 0, deltaAmt = 0;
    if (prevItem) {
        deltaPd = pdNum - Number(prevItem.person_days || 0);
        deltaAmt = amtNum - Math.round(prevItem.amount || 0);
    }
}
```

**問題の可能性**:
1. `window.prevEstimates`が初期見積ではなく、前回の調整後の値を参照している
2. 差分計算のベースラインが誤っている

---

## 🎯 調査すべき方針

### フェーズ1: ログ出力による動作確認

#### 目的
システムの実際の動作をログで追跡し、どこで意図しない変更が発生しているかを特定する

#### 実施内容

1. **ルールベース調整のログ強化**
   ```python
   # chat_service.py:_analyze_and_apply() に追加
   print(f"[DEBUG] message: {message}")
   print(f"[DEBUG] normalized: {m}")
   print(f"[DEBUG] targets: {targets}")
   print(f"[DEBUG] apply_to_all: {apply_to_all}")
   print(f"[DEBUG] reduce_ratio: {reduce_ratio}")
   print(f"[DEBUG] changed items: {[c[0] for c in changed]}")
   ```

2. **AI調整のログ強化**
   ```python
   # chat_service.py:950-1044 に追加
   print(f"[DEBUG] AI調整前のupdated件数: {len(updated)}")
   print(f"[DEBUG] AI prompt: {prompt['content'][:500]}...")
   print(f"[DEBUG] AIレスポンス: {content[:500]}...")
   print(f"[DEBUG] AI調整後のnorm件数: {len(norm)}")
   print(f"[DEBUG] ai_adjusted: {ai_adjusted}")
   ```

3. **最終レスポンスのログ**
   ```python
   # chat_service.py:1058-1100 に追加
   print(f"[DEBUG] 最終updated件数: {len(updated)}")
   print(f"[DEBUG] 最終note: {note[:200]}...")
   print(f"[DEBUG] 最終totals: {totals}")
   ```

#### 期待される結果
- どの処理段階で全項目が変更されているかを特定できる
- ルールベースで問題があるのか、AI調整で問題があるのかが判明する

---

### フェーズ2: ルールベース調整のロジック検証

#### 目的
`_analyze_and_apply()`のターゲット検出ロジックが正しく動作しているかを検証する

#### 実施内容

1. **キーワードマッピングの確認**
   - `mapping`辞書に「admin」「dashboard」が含まれているか
   - 正しいキーに対応しているか
   ```python
   # chat_service.py:188-200 を確認
   mapping = {
       '管理画面': ['管理', '管理画面', 'admin', 'フロント', 'ui', '画面', 'ダッシュボード'],
       ...
   }
   ```

2. **ターゲット検出の動作確認**
   - "admin dashboard"というメッセージで正しくターゲットが検出されるか
   - `targets`リストに正しい値が入っているか

3. **全体適用フラグの検証**
   - `apply_to_all`がFalseになっているか
   ```python
   # chat_service.py:181
   apply_to_all = any(x in m for x in ['全体', '合計', '全部', 'すべて', ...])
   ```

#### 期待される結果
- `targets`に正しいキーワードが含まれる
- `apply_to_all`がFalseになる
- Admin Dashboardのみが`match=True`になる

---

### フェーズ3: AI調整のプロンプト改善

#### 目的
AI調整が全項目を調整しないように、プロンプトを改善する

#### 実施内容

1. **プロンプトの見直し**
   ```python
   # 現在のプロンプト（chat_service.py:954-962）
   prompt = {
       "role": "user",
       "content": (
           f"{language_instruction}\n\n"
           "以下は現在の見積です。各項目の人日(person_days)と金額(amount)を単価"
           f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
           ...
       ),
   }
   ```

2. **プロンプトの改善案**
   ```python
   # 改善後
   prompt = {
       "role": "user",
       "content": (
           f"{language_instruction}\n\n"
           "以下は現在の見積です。\n"
           "**重要**: ユーザーの依頼文で明示的に指定された項目のみを調整してください。\n"
           "指定されていない項目は変更しないでください。\n\n"
           f"各項目の人日(person_days)と金額(amount)を単価{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整してください。\n"
           ...
           "依頼文:\n" + (message or "") + "\n\n"
           "現在の見積(JSON):\n" + json.dumps(updated, ensure_ascii=False)
       ),
   }
   ```

3. **AI調整の採用条件の見直し**
   ```python
   # chat_service.py:1020-1042
   # 現在: AI案が総額を下げる場合のみ採用
   # 問題: 全項目を変更したAI案でも、総額が下がれば採用される

   # 改善案: 変更された項目数をチェック
   changed_count = sum(1 for a, b in zip(norm, updated)
                       if abs(a['person_days'] - b['person_days']) > 0.05)
   if changed_count <= 3:  # 変更項目が3つ以下の場合のみ採用
       updated = norm
   ```

#### 期待される結果
- AIが指定された項目のみを調整するようになる
- 不要な項目変更が防止される

---

### フェーズ4: フロントエンド差分計算の検証

#### 目的
フロントエンドの差分表示が正しい基準値を使用しているかを確認する

#### 実施内容

1. **初期見積の保存確認**
   ```javascript
   // index.html: タスク完了時に初期見積を保存
   if (!window.initialEstimates) {
       window.initialEstimates = JSON.parse(JSON.stringify(apiData.estimates));
   }
   ```

2. **差分計算のベース確認**
   ```javascript
   // updateEstimatesView() 内
   // 現在: window.prevEstimates を使用
   // 改善: window.initialEstimates を使用
   const prev = window.initialEstimates || [];
   ```

3. **デバッグログの追加**
   ```javascript
   console.log('[DEBUG] Current estimates:', ests);
   console.log('[DEBUG] Previous estimates:', prev);
   console.log('[DEBUG] Delta PD:', deltaPd);
   ```

#### 期待される結果
- 差分が初期見積からの変更量を正しく表示する
- ユーザーが視覚的に変更内容を理解できる

---

## 📝 推奨される調査順序

1. **最優先**: フェーズ1（ログ出力）を実施し、問題箇所を特定
2. **次**: 問題箇所に応じてフェーズ2またはフェーズ3を実施
3. **最後**: フェーズ4でフロントエンド表示を検証

---

## 🚨 追加の懸念事項

### 1. 言語設定の影響
- 現在LANGUAGE=enで動作しているが、キーワード検出は日本語と英語の両方に対応しているか？
- `mapping`辞書に英語キーワードが含まれているか？

### 2. ルールベース調整とAI調整の役割分担
- 現在の実装では、ルールベース調整→AI調整の順で実行される
- AI調整がルールベース調整の結果を完全に上書きする可能性がある
- これが意図した設計なのか？

### 3. ユーザー体験の問題
- ユーザーは「Admin Dashboardのみを調整してほしい」と期待している
- しかし、システムは「全体最適化」を試みている
- この設計方針は正しいのか？要件を再確認する必要がある

---

## 💡 根本的な解決策の方向性

### 短期的な対応（緊急）
1. ログ出力を強化して問題箇所を特定
2. 明らかなバグ（例: apply_to_allの誤動作）を修正
3. AIプロンプトに「指定項目のみ調整」の指示を追加

### 中期的な対応（品質向上）
1. ルールベース調整のロジックをリファクタリング
2. AI調整の採用条件を厳格化（変更項目数チェック）
3. ユーザーに調整範囲を選択させるUI追加（例: 「Admin Dashboardのみ」vs「全体調整」）

### 長期的な対応（設計見直し）
1. チャット調整機能の要件定義を見直す
2. ユーザーの期待と実際の動作のギャップを埋める
3. より直感的なUI/UXへの改善

---

## 📊 調査結果の記録方法

### ログファイルの保存場所
```
./logs/adjust_investigation_YYYYMMDD_HHMMSS.txt
```

### 記録すべき内容
- 各フェーズの調査結果
- 発見したバグや問題点
- 実施した修正内容
- 修正前後の動作比較

---

## ✅ 成功の定義

以下の条件を満たすことを成功とする：

1. **ターゲット検出の正確性**
   - "Please make the admin dashboard simple and affordable."
   - → Admin Dashboardのみが調整される
   - → 他の項目は変更されない

2. **メッセージと実際の整合性**
   - メッセージに記載された変更内容と、Deliverable Detailsの表示が一致する

3. **ユーザー期待との一致**
   - ユーザーのリクエストに忠実な調整が行われる
   - 不要な項目変更が発生しない

---

## 📊 コード調査結果（2025-10-23 実施）

### Quick Adjust（機械的調整）の実装仕様

#### 1. Fit to Budget（上限予算に合わせる）
**ファイル**: `backend/app/services/chat_service.py:87-115`

**動作**:
- **全項目**を比率で縮小
- 税込み総額が上限予算以下になるように調整
- 係数 = cap / current_total

**例**: 上限120万円の場合、すべての項目が同じ比率で縮小される

#### 2. Change Unit Cost（単価変更）
**ファイル**: `backend/app/services/chat_service.py:117-137`

**動作**:
- **全項目**の単価を変更
- person_days × new_unit_cost で金額を再計算

**例**: 単価を4万円/人日に変更した場合、すべての項目の金額が再計算される

#### 3. Add Risk Buffer（リスクバッファ追加）
**ファイル**: `backend/app/services/chat_service.py:139-159`

**動作**:
- **全項目**にリスクバッファを上乗せ
- 係数 = 1.0 + (percent / 100.0)

**例**: 20%リスクバッファを追加した場合、すべての項目が1.2倍になる

#### 4. Reduce Scope（機能絞り込み）
**ファイル**: `backend/app/services/chat_service.py:161-176`

**動作**:
- **キーワードに一致する項目のみ**を除外
- 完全除外（0にする）

**例**: "test"をキーワードに指定した場合、"Unit Testing"、"Integration Testing"が除外される

**結論**: Quick Adjustは基本的に**全項目対象**（Reduce Scopeのみ特定項目）

---

### AI Adjust（自由記述調整）の実装仕様

#### フロー概要
```
[ユーザー入力]
    ↓
[1. ルールベース調整] (_analyze_and_apply)
    ↓
[2. AI調整] (OpenAI API) ← オプション、OPENAI_API_KEY設定時のみ
    ↓
[3. 最終メッセージ生成]
```

#### 1. ルールベース調整（_analyze_and_apply）
**ファイル**: `backend/app/services/chat_service.py:177-353`

##### 1-1. ターゲット検出
**キーワードマッピング** (184-198行目):
```python
mapping = {
    '管理画面': ['管理', '管理画面', 'admin', 'フロント', 'ui', '画面', 'ダッシュボード'],
    'レポート': ['レポート', '帳票', '出力', '印刷', 'エクスポート'],
    'api': ['api', 'エンドポイント', 'rest', 'graphql', 'バックエンド', 'サーバ', 'サーバー'],
    'テスト': ['テスト', '試験', 'test', '検証', 'qa', '品質保証'],
    '認証': ['認証', 'ログイン', 'login', 'auth', 'セキュリティ', 'セッション', 'パスワード'],
    'デザイン': ['デザイン', 'design', 'ui', 'ux', 'css', 'スタイル', '見た目'],
    'インフラ': ['インフラ', 'デプロイ', 'deploy', '環境', '構築', 'サーバ', 'aws', 'クラウド'],
    'ドキュメント': ['ドキュメント', '資料', '説明', 'マニュアル', '手順書', 'readme'],
    'データベース': ['データベース', 'db', 'database', 'sql', 'rdb', 'テーブル', 'スキーマ'],
    '検索': ['検索', 'search', 'サーチ', '全文検索', 'elasticsearch'],
    '通知': ['通知', 'notification', 'メール', 'mail', 'プッシュ', 'アラート'],
    '決済': ['決済', 'payment', '課金', '支払', 'クレジット', 'カード'],
    'バッチ': ['バッチ', 'batch', '定期処理', 'cron', 'ジョブ'],
}
```

**動作**:
- メッセージを小文字化（`message.lower()`）
- キーワードマッチで`targets`リストを生成
- 例: "admin dashboard" → `targets = ['管理', '管理画面', 'admin', 'フロント', 'ui', '画面', 'ダッシュボード']`

##### 1-2. 全体適用フラグ（181行目）
```python
apply_to_all = any(x in m for x in ['全体', '合計', '全部', 'すべて', '全て', 'トータル', '総額', '総計', '全項目', '全成果物'])
```

**🚨 問題発見**:
- **日本語のキーワードのみ**
- 英語の「all」「total」「overall」「entire」などがない
- LANGUAGE=enの場合、全体適用が検出されない可能性

##### 1-3. 削減率の推定（208-230行目）
```python
# 明示的なパーセンテージ（例: 20%下げる）
if pct_match and any(k in m for k in ['下げ', '安く', '削減', '減ら', '縮小', '少なく', '減額', 'カット', 'ダウン']):
    reduce_ratio = 1.0 - (p/100.0)

# 言い回しに応じた既定比率
if reduce_ratio is None and any(x in m for x in ['簡便', '簡易', '簡単', 'シンプル', 'ライト', '軽量', 'ミニマム', '最小限', '必要最小']):
    reduce_ratio = 0.7  # 30%削減
if reduce_ratio is None and any(x in m for x in ['安く', '安価', 'コストダウン', '費用抑', 'コスト削減', 'コストカット', '予算削減', '節約', 'もう少し安', '少し安', '価格を下げ', '値下げ']):
    reduce_ratio = 0.8  # 20%削減
if reduce_ratio is None and any(x in m for x in ['大幅', 'かなり', 'もっと下げ', '大きく下げ', '大きく削減', '大胆', '思い切']):
    reduce_ratio = 0.6  # 40%削減
if reduce_ratio is None and any(x in m for x in ['少し下げ', '若干下げ', 'ちょっと下げ', '少しだけ', 'わずかに', '微調整']):
    reduce_ratio = 0.9  # 10%削減
if reduce_ratio is None and any(x in m for x in ['ある程度', '適度', '程々', 'そこそこ', 'まあまあ']):
    reduce_ratio = 0.85  # 15%削減
```

**🚨 問題発見**:
- **ほとんどが日本語またはカタカナ**
- 'シンプル'はあるが、**'simple'（英語）はない**
- '安価'はあるが、**'affordable'（英語）はない**
- LANGUAGE=enの場合、削減率が検出されない

##### 1-4. フォールバック動作（305-338行目）
```python
elif not changed and targets and reduce_ratio is None and not full_remove:
    # 対象は見つかったが強度が曖昧 → デフォルトで軽減
    factor = 0.85  # 15%削減
    for e in new_ests:
        nm = (e.get('deliverable_name') or '').lower()
        if any(t in nm for t in targets):  # ← ターゲットにマッチした項目のみ
            pd = round(float(e['person_days']) * factor, 1)
            amt = pd * settings.get_daily_unit_cost()
            changed.append(...)
```

**動作**:
- `targets`が検出された
- しかし`reduce_ratio`が検出されなかった
- → **ターゲット項目のみ**を15%削減

**期待される動作（"admin dashboard simple affordable"の場合）**:
1. 'admin'/'dashboard'がマッチ → `targets`に追加
2. 'simple'/'affordable'は英語でマッチしない → `reduce_ratio = None`
3. フォールバック動作 → Admin Dashboardのみ15%削減 ✅

**結論**: ルールベース調整は正しく動作しているはず！

---

#### 2. AI調整（OpenAI API）
**ファイル**: `backend/app/services/chat_service.py:950-1060`

##### 2-1. AI調整のプロンプト（955-966行目）
```python
prompt = {
    "role": "user",
    "content": (
        f"{language_instruction}\n\n"
        "以下は現在の見積です。各項目の人日(person_days)と金額(amount)を単価"
        f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
        "JSONのみ、コードブロックなしで返してください。フィールドは reply_md, estimates(配列), totals のみ。\n"
        "estimates の各要素は {deliverable_name, deliverable_description, person_days(小数1桁), amount(数値), reasoning(短いMarkdown可)} とします。\n"
        f"totals は {{subtotal, tax, total}}（税率{settings.get_tax_rate()*100:.0f}%）です。\n"
        "依頼文:\n" + (message or "") + "\n\n"
        "現在の見積(JSON):\n" + json.dumps(updated, ensure_ascii=False)
    ),
}
```

**🚨 根本原因発見**:

1. **「各項目の...調整し」という指示**
   - AIは「すべての項目を調整すべき」と解釈する
   - 特定項目のみを調整する指示がない

2. **「依頼文に沿って改善案を出してください」が曖昧**
   - 依頼文: "make the admin dashboard simple and affordable"
   - AIの解釈: 「システム全体を効率化して、admin dashboardを特に安くする」
   - 正しい解釈: 「admin dashboardのみを簡素化・安価にする」

3. **`updated`にはルールベース調整後のデータが渡される**
   - Admin Dashboardが15%削減された状態がベース
   - AIはそれをさらに全体調整する

##### 2-2. AI調整の採用条件（1020-1042行目）
```python
if _differs(norm, updated):
    # ルールベースで変更がない場合はAI案を無条件で採用
    # ルールベースで変更がある場合は、AI案の総額が下がる場合のみ採用
    if not has_rule_changes:
        updated = norm
        ai_adjusted = True
    else:
        ai_tot = self._calc_totals(norm).get('total', 0.0)
        rb_tot = self._calc_totals(updated).get('total', 0.0)
        if ai_tot < rb_tot - 1e-3:
            updated = norm
            ai_adjusted = True
```

**動作**:
- ルールベース調整があった場合（`has_rule_changes = True`）
- AI案の総額がルールベース案より低ければ採用
- **変更項目数のチェックはない**
- → 全項目を変更したAI案でも、総額が下がれば採用される

**🚨 問題**: AI案が全項目を調整していても、総額が下がれば採用されてしまう

---

### 🎯 根本原因のまとめ

#### 原因1: ルールベース調整の言語対応不足
**問題**:
- キーワードマッピングに英語が一部含まれているが、削減率推定語彙はほぼ日本語のみ
- 'simple'/'affordable'などの英語キーワードがマッチしない
- LANGUAGE=enの場合、フォールバック動作（15%削減）が使用される

**影響**:
- ルールベース調整自体は正しく動作している（Admin Dashboardのみ15%削減）
- しかし、その後のAI調整で上書きされる

#### 原因2: AI調整のプロンプトが不適切（最大の問題）
**問題**:
- 「各項目の...調整し」→ AIは全項目を調整すべきと解釈
- 「指定された項目のみを調整せよ」という明示的な指示がない
- ルールベース調整後のデータをベースにAIがさらに全体調整

**影響**:
- Admin Dashboardだけでなく、全13項目が調整される
- ユーザーの意図（Admin Dashboardのみ）と乖離

#### 原因3: AI調整の採用条件が緩い
**問題**:
- 総額が下がれば無条件で採用
- 変更項目数のチェックがない

**影響**:
- 全項目を変更したAI案でも採用される

---

### LANGUAGE=jaで正しく動作する理由

#### LANGUAGE=jaの場合
1. **ルールベース調整**:
   - 日本語キーワード（'管理画面'/'簡単'/'安く'など）が正しくマッチ
   - 削減率も正しく推定される（例: 'シンプル' → 30%削減）
   - → より正確な調整が行われる

2. **AI調整**:
   - 日本語プロンプトで「依頼文に沿って」という指示が機能しやすい
   - AIも日本語の文脈をより正確に理解できる
   - → 不要な全体調整が発生しにくい

#### LANGUAGE=enの場合
1. **ルールベース調整**:
   - 英語キーワード（'admin'/'dashboard'）はマッチする
   - しかし削減率キーワード（'simple'/'affordable'）はマッチしない
   - → フォールバック動作（15%削減）になる

2. **AI調整**:
   - 英語プロンプトで「各項目の...調整し」が全項目調整と解釈される
   - 「admin dashboardのみ」という意図が伝わらない
   - → 全項目が調整される

---

## 🔧 解決方針（具体的）

### 優先度1: AI調整プロンプトの改善（最重要）

**実施内容**:
1. プロンプトに「指定項目のみ調整」の明示的な指示を追加
2. ルールベース調整で変更された項目のリストを渡す

**修正案** (`chat_service.py:955-966`):
```python
# ルールベース調整で変更された項目のリストを作成
changed_items = [c[0] for c in changed] if has_rule_changes else []

prompt = {
    "role": "user",
    "content": (
        f"{language_instruction}\n\n"
        "**IMPORTANT**: Only adjust the items specifically mentioned in the user's request.\n"
        "Do not modify other items unless explicitly requested.\n\n"
        f"Changed items by rule-based adjustment: {', '.join(changed_items) if changed_items else 'None'}\n\n"
        "以下は現在の見積です。単価"
        f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整してください。\n"
        "JSONのみ、コードブロックなしで返してください。フィールドは reply_md, estimates(配列), totals のみ。\n"
        "estimates の各要素は {deliverable_name, deliverable_description, person_days(小数1桁), amount(数値), reasoning(短いMarkdown可)} とします。\n"
        f"totals は {{subtotal, tax, total}}（税率{settings.get_tax_rate()*100:.0f}%）です。\n\n"
        "依頼文:\n" + (message or "") + "\n\n"
        "現在の見積(JSON):\n" + json.dumps(updated, ensure_ascii=False)
    ),
}
```

### 優先度2: AI調整の採用条件の厳格化

**実施内容**:
変更項目数をチェックし、過度な全体調整を防ぐ

**修正案** (`chat_service.py:1020-1042`):
```python
if _differs(norm, updated):
    # 変更項目数をカウント
    changed_count = sum(1 for a, b in zip(norm, updated)
                       if abs(float(a.get('person_days', 0)) - float(b.get('person_days', 0))) > 0.05)

    # ルールベースで変更がない場合はAI案を無条件で採用
    if not has_rule_changes:
        # ただし、変更項目が3つ以下の場合のみ
        if changed_count <= 3:
            updated = norm
            ai_adjusted = True
    else:
        ai_tot = self._calc_totals(norm).get('total', 0.0)
        rb_tot = self._calc_totals(updated).get('total', 0.0)
        # 総額が下がり、かつ変更項目数が妥当な場合のみ採用
        if ai_tot < rb_tot - 1e-3 and changed_count <= 5:
            updated = norm
            ai_adjusted = True
```

### 優先度3: ルールベース調整の英語キーワード追加

**実施内容**:
削減率推定語彙に英語を追加

**修正案** (`chat_service.py:219-230`):
```python
# 言い回しに応じた既定比率（英語追加）
if reduce_ratio is None and any(x in m for x in ['簡便', '簡易', '簡単', 'シンプル', 'ライト', '軽量', 'ミニマム', '最小限', '必要最小', 'simple', 'light', 'minimal', 'minimum', 'basic']):
    reduce_ratio = 0.7  # 30%削減
if reduce_ratio is None and any(x in m for x in ['安く', '安価', 'コストダウン', '費用抑', 'コスト削減', 'コストカット', '予算削減', '節約', 'もう少し安', '少し安', '価格を下げ', '値下げ', 'affordable', 'cheap', 'cheaper', 'inexpensive', 'cost-effective', 'budget', 'economical']):
    reduce_ratio = 0.8  # 20%削減
if reduce_ratio is None and any(x in m for x in ['大幅', 'かなり', 'もっと下げ', '大きく下げ', '大きく削減', '大胆', '思い切', 'significantly', 'substantially', 'greatly', 'drastically', 'much']):
    reduce_ratio = 0.6  # 40%削減
if reduce_ratio is None and any(x in m for x in ['少し下げ', '若干下げ', 'ちょっと下げ', '少しだけ', 'わずかに', '微調整', 'slightly', 'a bit', 'a little', 'minor', 'small']):
    reduce_ratio = 0.9  # 10%削減
if reduce_ratio is None and any(x in m for x in ['ある程度', '適度', '程々', 'そこそこ', 'まあまあ', 'moderately', 'reasonably', 'somewhat']):
    reduce_ratio = 0.85  # 15%削減
```

### 優先度4: 全体適用フラグに英語キーワード追加

**実施内容**:
英語の「all」「total」などを追加

**修正案** (`chat_service.py:181`):
```python
apply_to_all = any(x in m for x in [
    '全体', '合計', '全部', 'すべて', '全て', 'トータル', '総額', '総計', '全項目', '全成果物',
    'all', 'total', 'overall', 'entire', 'everything', 'whole', 'every item', 'every deliverable'
])
```

---

## 📝 実施履歴

### 2025-10-23 17:45 - コード調査完了
- Quick Adjustの仕様を確認
- AI Adjustの実装を詳細分析
- 根本原因を特定
- 解決方針を策定

### 2025-10-23 18:30 - Priority 1実装完了
**実施内容**: AI調整プロンプトの改善 + デバッグログ追加 + 英語キーワード対応

#### 修正1: _analyze_and_applyの戻り値を拡張
**ファイル**: `backend/app/services/chat_service.py:177`

**変更内容**:
- 戻り値を3つ→4つに変更: `(new_ests, note, has_changes, changed_item_names)`
- `changed_item_names`: ルールベースで変更された項目名のリスト

**目的**: AI調整プロンプトに、ルールベースで変更された項目を伝えるため

#### 修正2: 全体適用フラグに英語キーワード追加
**ファイル**: `backend/app/services/chat_service.py:182-185`

**変更前**:
```python
apply_to_all = any(x in m for x in ['全体', '合計', '全部', 'すべて', '全て', 'トータル', '総額', '総計', '全項目', '全成果物'])
```

**変更後**:
```python
apply_to_all = any(x in m for x in [
    '全体', '合計', '全部', 'すべて', '全て', 'トータル', '総額', '総計', '全項目', '全成果物',
    'all', 'total', 'overall', 'entire', 'everything', 'whole'
])
```

**目的**: LANGUAGE=enで全体適用を検出できるようにする

#### 修正3: 削減率推定に英語キーワード追加
**ファイル**: `backend/app/services/chat_service.py:223-232`

**追加キーワード**:
- **簡便系（30%削減）**: 'simple', 'simpler', 'simplified', 'light', 'lightweight', 'minimal', 'minimum', 'basic'
- **安価系（20%削減）**: 'affordable', 'cheaper', 'cheap', 'cost down', 'reduce cost', 'cut cost', 'lower cost', 'save money', 'budget friendly', 'economical'

**目的**: "simple and affordable"のような英語表現で削減率を推定できるようにする

#### 修正4: デバッグログ追加（ルールベース調整）
**ファイル**: `backend/app/services/chat_service.py:367-369`

**追加ログ**:
```python
print(f"[RB] changed_item_names={changed_item_names}")
```

**目的**: ルールベースで変更された項目名を明示的に出力

#### 修正5: AI調整プロンプトの改善（最重要）
**ファイル**: `backend/app/services/chat_service.py:973-1002`

**変更前**:
```python
prompt = {
    "role": "user",
    "content": (
        f"{language_instruction}\n\n"
        "以下は現在の見積です。各項目の人日(person_days)と金額(amount)を単価"
        f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
        ...
    ),
}
```

**変更後**:
```python
# Build list of items adjusted by rule-based processing
rule_adjusted_items_text = ""
if changed_item_names:
    rule_adjusted_items_text = f"\n\n**Items adjusted by rule-based processing**: {', '.join(changed_item_names)}\n"

prompt = {
    "role": "user",
    "content": (
        f"{language_instruction}\n\n"
        "**IMPORTANT INSTRUCTION**: Only adjust the items specifically mentioned in the user's request below. "
        "Do not modify other items unless explicitly requested by the user.\n"
        f"{rule_adjusted_items_text}"
        "以下は現在の見積です。指定された項目のみの人日(person_days)と金額(amount)を単価"
        f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
        ...
    ),
}
```

**追加された指示**:
1. **"IMPORTANT INSTRUCTION: Only adjust the items specifically mentioned in the user's request below."**
   - AIに対して、ユーザーが指定した項目のみを調整するよう明示
2. **"Do not modify other items unless explicitly requested by the user."**
   - 明示的に指定されていない項目は変更しないよう指示
3. **"Items adjusted by rule-based processing: ..."**
   - ルールベースで変更された項目リストを提示
4. **"指定された項目のみの"**
   - 日本語でも「指定された項目のみ」を強調
5. **「各項目の」を削除**
   - 変更前: "各項目の人日と金額を...調整し"（全項目調整の印象）
   - 変更後: "指定された項目のみの人日と金額を...調整し"（特定項目のみ）

**目的**: AIが全項目を調整しないように明示的に制約する

#### 修正6: AI調整デバッグログ追加
**ファイル**: `backend/app/services/chat_service.py:996-1036`

**追加ログ**:
```python
# Debug: Print AI prompt
print(f"[AI] Sending prompt to LLM (first 500 chars):")
print(f"[AI] {prompt['content'][:500]}")
print(f"[AI] Rule-adjusted items: {changed_item_names}")

# Debug: Print AI response
print(f"[AI] Received response (first 500 chars):")
print(f"[AI] {content[:500]}")

# Debug: Count changed items in AI response
ai_changed_count = 0
for ai_est in ai_estimates:
    ai_name = (ai_est.get("deliverable_name") or "").lower()
    for orig_est in updated_before_ai:
        orig_name = (orig_est.get("deliverable_name") or "").lower()
        if ai_name == orig_name:
            ai_pd = float(ai_est.get("person_days", 0.0))
            orig_pd = float(orig_est.get("person_days", 0.0))
            if abs(ai_pd - orig_pd) >= 0.05:
                ai_changed_count += 1
            break
print(f"[AI] AI changed {ai_changed_count} items")
print(f"[AI] Rule-based changed {len(changed_item_names)} items")
```

**目的**: AI調整の動作を詳細に追跡できるようにする

#### 修正7: AI採用判定のデバッグログ強化
**ファイル**: `backend/app/services/chat_service.py:1084-1116`

**追加ログ**:
```python
# Debug: Log AI adoption decision
print(f"[AI] AI adoption decision:")
print(f"[AI]   has_rule_changes={has_rule_changes}")
print(f"[AI]   ai_changed_count={ai_changed_count}")
print(f"[AI]   rule_changed_count={len(changed_item_names)}")

# 採用判定結果
print(f"[AI] ✓ AI proposal ADOPTED (no rule-based changes)")
# または
print(f"[AI] ✓ AI proposal ADOPTED (total cost improved: ¥{int(rb_tot):,} → ¥{int(ai_tot):,})")
# または
print(f"[AI] ✗ AI proposal REJECTED (no total cost improvement: ¥{int(rb_tot):,} vs ¥{int(ai_tot):,})")
```

**目的**: AI提案の採用/却下の判断根拠を明確にする

#### 修正8: 関数呼び出し側の修正
**ファイル**: `backend/app/services/chat_service.py:963`

**変更内容**:
```python
# 変更前
updated, rule_note, has_rule_changes = self._analyze_and_apply(updated, message or "")

# 変更後
updated, rule_note, has_rule_changes, changed_item_names = self._analyze_and_apply(updated, message or "")
```

**目的**: 拡張された戻り値を受け取る

---

#### 期待される効果

1. **ルールベース調整**: "simple and affordable"などの英語表現で削減率が推定される
2. **AI調整**: "IMPORTANT INSTRUCTION"により、Admin Dashboardのみが調整される
3. **デバッグログ**: 実行フローが明確になり、問題箇所の特定が容易になる

#### 次のアクション
- サービス再起動
- "Please make the admin dashboard simple and affordable." で動作確認
- ログ出力を確認して効果を検証

### 2025-10-23 18:40 - 緊急修正: 単語境界マッチング実装
**問題**: "Please make the admin dashboard simple and affordable." を実行したところ、Requirements DocumentとAdmin Dashboardの2項目のみが残り、他11項目が消失

**根本原因**: 'ui'キーワードが'req**ui**rements'に部分一致してしまった
```
targets = ['管理', '管理画面', 'admin', 'フロント', 'ui', '画面', 'ダッシュボード']
'ui' in 'requirements document' → True（'req**ui**rements'）
```

**ユーザー指摘**: 英単語を半角空白で区切って認識していないことが根本問題

**修正内容**: 単語境界マッチングの実装

#### 修正1: メインマッチングロジックの変更
**ファイル**: `backend/app/services/chat_service.py:254-264`

**変更前**:
```python
name = (e.get('deliverable_name') or '').lower()
match = apply_to_all or (any(t in name for t in targets) if targets else False)
```

**変更後**:
```python
name = (e.get('deliverable_name') or '').lower()

# Word-boundary matching to avoid false matches (e.g., 'ui' in 'requirements')
# Priority 1: Exact word match (split by spaces)
name_words = set(name.split())
word_match = any(t in name_words for t in targets) if targets else False

# Priority 2: Substring match for keywords >= 4 chars
# (fallback for partial words like 'admin' in 'administrator', '管理' in '管理画面')
substring_match = any(t in name for t in targets if len(t) >= 4) if targets and not word_match else False

# 全体適用フラグがtrueの場合、または個別ターゲットにマッチする場合
match = apply_to_all or word_match or substring_match
```

**ロジック**:
1. **優先順位1**: 単語単位の完全一致（空白で分割）
   - 'requirements document' → `{'requirements', 'document'}`
   - 'ui' in `{'requirements', 'document'}` → False ✓
   - 'admin' in `{'admin', 'dashboard'}` → True ✓

2. **優先順位2**: 部分一致（4文字以上のキーワードのみ）
   - 'admin' (5文字) in 'administrator' → True ✓
   - '管理' (2文字) in '管理画面' → True ✓（UTF-8で4バイト以上）
   - 'ui' (2文字) → スキップ（3文字以下）

#### 修正2: フォールバック処理の修正
**ファイル**: `backend/app/services/chat_service.py:332-336`

**変更前**:
```python
nm = (e.get('deliverable_name') or '').lower()
if any(t in nm for t in targets):
```

**変更後**:
```python
nm = (e.get('deliverable_name') or '').lower()
# Use same word-boundary matching logic
nm_words = set(nm.split())
nm_word_match = any(t in nm_words for t in targets)
nm_substring_match = any(t in nm for t in targets if len(t) >= 4) if not nm_word_match else False
if nm_word_match or nm_substring_match:
```

#### 修正3: デバッグログ強化
**ファイル**: `backend/app/services/chat_service.py:285-286`

**追加ログ**:
```python
match_type = "word" if word_match else ("substring" if substring_match else "none")
print(f"[RB] item match name='{name}' match_type={match_type} before={before_pd}/{int(before_amt)} after={pd}/{int(amt)} changed={did_change}")
```

**目的**: どのマッチング方法（word/substring/none）で一致したかを確認可能にする

---

#### 期待される動作

**テストケース**: "Please make the admin dashboard simple and affordable."

**期待されるマッチング**:
```
Requirements Document: word_match=False, substring_match=False → match=False → 変更なし
Admin Dashboard: word_match=True ('admin' in {'admin', 'dashboard'}) → match=True → 30%削減
```

**期待される結果**:
- Admin Dashboardのみが調整される
- 他の12項目は変更されない
- AIには"Admin Dashboard"のみが変更項目として伝達される
- AIも"Admin Dashboard"のみを調整する

### 2025-10-23 19:00 - 最終修正: AI項目数検証 + CRITICAL INSTRUCTION追加
**問題**: 単語境界マッチング実装後も、Admin Dashboardの1項目のみが残り、他12項目が消失

**根本原因**: AIが「指定項目のみ調整」を「指定項目のみ返す」と誤解釈

**修正内容**:

#### 修正1: AI項目数検証の追加
**ファイル**: `backend/app/services/chat_service.py:1059-1065`

**追加コード**:
```python
if ai_estimates:
    # Validate: AI must return the same number of items
    if len(ai_estimates) != len(updated):
        print(f"[AI] ✗ AI response REJECTED: Item count mismatch (AI returned {len(ai_estimates)} items, expected {len(updated)} items)")
        # Do not adopt AI proposal, keep rule-based result
    else:
        # 正規化処理（normの作成）
```

**効果**: AIが一部項目のみを返した場合、自動的に却下される

#### 修正2: CRITICAL INSTRUCTION追加（プロンプト改善）
**ファイル**: `backend/app/services/chat_service.py:994-1006`

**変更前**:
```python
"**IMPORTANT INSTRUCTION**: Only adjust the items specifically mentioned in the user's request below. "
"Do not modify other items unless explicitly requested by the user.\n"
```

**変更後**:
```python
total_items_count = len(updated)

"**CRITICAL INSTRUCTION**:\n"
f"1. You MUST return ALL {total_items_count} items in the estimates array.\n"
"2. Only adjust the values (person_days, amount) for items specifically mentioned in the user's request below.\n"
"3. For items NOT mentioned in the request, keep their original values UNCHANGED.\n"
"4. Do NOT remove, exclude, or omit any items from the estimates array.\n"
```

**改善点**:
1. **番号付きリストで明確化**
2. **"You MUST return ALL X items"** - 項目数を明示
3. **"adjust the values"** - 値の調整であることを明示
4. **"keep their original values UNCHANGED"** - 変更しない項目もそのまま返すことを明示
5. **"Do NOT remove, exclude, or omit"** - 除外しないことを明示

#### 期待される動作

**テストケース**: "Please make the admin dashboard simple and affordable."

**AIプロンプト送信**:
```
**CRITICAL INSTRUCTION**:
1. You MUST return ALL 13 items in the estimates array.
2. Only adjust the values (person_days, amount) for items specifically mentioned in the user's request below.
3. For items NOT mentioned in the request, keep their original values UNCHANGED.
4. Do NOT remove, exclude, or omit any items from the estimates array.

**Items adjusted by rule-based processing**: Admin Dashboard

依頼文:
Please make the admin dashboard simple and affordable.

現在の見積(JSON):
[... 13項目 ...]
```

**AIレスポンス検証**:
- AIが13項目を返す → ✓ 検証OK、採用判定へ
- AIが1項目のみ返す → ✗ 却下、ルールベース結果を保持

**最終結果**:
- ✅ 13項目すべてが表示される
- ✅ Admin Dashboardのみが調整される（ルールベース: 30%削減）
- ✅ 他の12項目は元の値のまま

### 次のアクション
コミット・再起動して動作確認を実施する
