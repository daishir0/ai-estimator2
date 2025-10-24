# ユーザー画面に表示される日本語メッセージ一覧

**作成日**: 2025-10-24
**目的**: LANGUAGE=enの際にユーザー画面に表示される日本語メッセージを特定し、多言語対応を実施する

---

## 📋 対象箇所（15箇所）

### 🔴 chat_service.py（5箇所）

#### 1. Line 115: 上限予算調整の説明メッセージ
**現在のコード**:
```python
note = f"総額 {int(current):,} 円 → {int(self._calc_totals(out)['total']):,} 円（上限 {int(cap):,} 円に合わせ係数 {ratio:.2f} を適用）"
```

**表示タイミング**: クイック調整「上限予算に合わせる」実行時
**影響**: APIレスポンスとして返され、フロントエンドに表示される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.budget_cap_summary": "Total ${current} → ${new} (adjusted to cap ${cap} with factor {ratio})"
"messages.budget_cap_summary": "総額 {current} 円 → {new} 円（上限 {cap} 円に合わせ係数 {ratio} を適用）"

# コード修正
note = t('messages.budget_cap_summary').replace('{current}', f'{int(current):,}').replace('{new}', f'{int(self._calc_totals(out)["total"]):,}').replace('{cap}', f'{int(cap):,}').replace('{ratio}', f'{ratio:.2f}')
```

---

#### 2. Line 1056: 見積り未作成エラーメッセージ
**現在のコード**:
```python
return {"reply_md": "まだ見積りが作成されていません。まずはExcelをアップロードして実行してください。"}
```

**表示タイミング**: 見積り作成前にチャット調整を試みた時
**影響**: チャット画面にエラーメッセージとして表示

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.estimate_not_created": "Estimate has not been created yet. Please upload an Excel file and execute first."
"messages.estimate_not_created": "まだ見積りが作成されていません。まずはExcelをアップロードして実行してください。"

# コード修正
return {"reply_md": t('messages.estimate_not_created')}
```

---

#### 3. Line 1114: 調整方向テキスト
**現在のコード**:
```python
direction_text = '削減' if adjustment_request['direction'] == 'reduce' else '増額'
```

**表示タイミング**: 金額調整提案生成時
**影響**: 次の行（Line 1115）のメッセージで使用

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.direction_reduce": "reduction"
"messages.direction_reduce": "削減"
"messages.direction_increase": "increase"
"messages.direction_increase": "増額"

# コード修正
direction_text = t('messages.direction_reduce') if adjustment_request['direction'] == 'reduce' else t('messages.direction_increase')
```

---

#### 4. Line 1115: 提案メッセージ
**現在のコード**:
```python
reply_md = f"約{adjustment_request['amount']:,}円の{direction_text}案を3つご提案いたします。\n\n以下から最適な案をお選びください。"
```

**表示タイミング**: 金額調整提案が成功した時
**影響**: チャット画面にメッセージとして表示

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.proposal_generated": "We propose 3 {direction} options of approximately ${amount}.\n\nPlease select the most suitable option."
"messages.proposal_generated": "約{amount}円の{direction}案を3つご提案いたします。\n\n以下から最適な案をお選びください。"

# コード修正
reply_md = t('messages.proposal_generated').replace('{amount}', f'{adjustment_request["amount"]:,}').replace('{direction}', direction_text)
```

---

#### 5. Line 1155: 提案生成失敗エラーメッセージ
**現在のコード**:
```python
reply_md = "提案の生成に失敗しました。従来の調整方法をお試しください。"
```

**表示タイミング**: 金額調整提案の生成が失敗した時
**影響**: チャット画面にエラーメッセージとして表示

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.proposal_generation_failed": "Proposal generation failed. Please try the traditional adjustment method."
"messages.proposal_generation_failed": "提案の生成に失敗しました。従来の調整方法をお試しください。"

# コード修正
reply_md = t('messages.proposal_generation_failed')
```

---

### 🔴 input_service.py（5箇所）

#### 6. Line 18: Excel列数不足エラー
**現在のコード**:
```python
raise ValueError("Excelファイルには少なくとも2列（成果物名称、説明）が必要です。")
```

**表示タイミング**: Excel読み込み時、列数が2未満の場合
**影響**: APIエラーレスポンスとして返され、フロントエンドにエラー表示

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.excel_min_columns": "Excel file must have at least 2 columns (deliverable name, description)."
"messages.excel_min_columns": "Excelファイルには少なくとも2列（成果物名称、説明）が必要です。"

# コード修正
raise ValueError(t('messages.excel_min_columns'))
```

---

#### 7. Line 37: Excel読み込み失敗エラー
**現在のコード**:
```python
raise ValueError(f"Excelファイルの読み込みに失敗しました: {e}")
```

**表示タイミング**: Excel読み込み時、ファイル破損等のエラー発生時
**影響**: APIエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.excel_load_failed": "Failed to load Excel file: {error}"
"messages.excel_load_failed": "Excelファイルの読み込みに失敗しました: {error}"

# コード修正
raise ValueError(t('messages.excel_load_failed').replace('{error}', str(e)))
```

---

#### 8. Line 48: CSV列数不足エラー
**現在のコード**:
```python
raise ValueError("CSVファイルには少なくとも2列（成果物名称、説明）が必要です。")
```

**表示タイミング**: CSV読み込み時、列数が2未満の場合
**影響**: APIエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.csv_min_columns": "CSV file must have at least 2 columns (deliverable name, description)."
"messages.csv_min_columns": "CSVファイルには少なくとも2列（成果物名称、説明）が必要です。"

# コード修正
raise ValueError(t('messages.csv_min_columns'))
```

---

#### 9. Line 67: CSV読み込み失敗エラー
**現在のコード**:
```python
raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}")
```

**表示タイミング**: CSV読み込み時、ファイル破損等のエラー発生時
**影響**: APIエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.csv_load_failed": "Failed to load CSV file: {error}"
"messages.csv_load_failed": "CSVファイルの読み込みに失敗しました: {error}"

# コード修正
raise ValueError(t('messages.csv_load_failed').replace('{error}', str(e)))
```

---

#### 10. Line 90: 成果物データ解析失敗エラー
**現在のコード**:
```python
raise ValueError(f"成果物データの解析に失敗しました: {e}")
```

**表示タイミング**: 成果物データのパース時、形式不正等のエラー発生時
**影響**: APIエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.deliverable_parse_failed": "Failed to parse deliverable data: {error}"
"messages.deliverable_parse_failed": "成果物データの解析に失敗しました: {error}"

# コード修正
raise ValueError(t('messages.deliverable_parse_failed').replace('{error}', str(e)))
```

---

### 🔴 tasks.py（5箇所）

#### 11. Line 88: ファイル形式エラー
**現在のコード**:
```python
raise HTTPException(
    status_code=400,
    detail="Excel（.xlsx, .xls）またはCSV（.csv）ファイルのみアップロード可能です"
)
```

**表示タイミング**: 非対応ファイルアップロード時
**影響**: HTTPエラーレスポンスとして返され、フロントエンドにエラー表示

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.invalid_file_type": "Only Excel (.xlsx, .xls) or CSV (.csv) files can be uploaded"
"messages.invalid_file_type": "Excel（.xlsx, .xls）またはCSV（.csv）ファイルのみアップロード可能です"

# コード修正
raise HTTPException(status_code=400, detail=t('messages.invalid_file_type'))
```

---

#### 12. Line 127: JSON解析失敗エラー
**現在のコード**:
```python
raise HTTPException(status_code=400, detail="成果物データのJSON解析に失敗しました")
```

**表示タイミング**: Webフォームからの成果物データJSON解析失敗時
**影響**: HTTPエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.json_parse_failed": "Failed to parse deliverable data JSON"
"messages.json_parse_failed": "成果物データのJSON解析に失敗しました"

# コード修正
raise HTTPException(status_code=400, detail=t('messages.json_parse_failed'))
```

---

#### 13. Line 136: ファイル/データ未指定エラー
**現在のコード**:
```python
raise HTTPException(
    status_code=400,
    detail="ファイルまたは成果物データを指定してください"
)
```

**表示タイミング**: タスク作成時、ファイルもデータも指定されていない場合
**影響**: HTTPエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.file_or_data_required": "Please specify a file or deliverable data"
"messages.file_or_data_required": "ファイルまたは成果物データを指定してください"

# コード修正
raise HTTPException(status_code=400, detail=t('messages.file_or_data_required'))
```

---

#### 14. Line 211: タスク処理開始メッセージ
**現在のコード**:
```python
return {"message": "タスク処理を開始しました", "task_id": task_id}
```

**表示タイミング**: タスク作成成功時
**影響**: APIレスポンスとして返され、フロントエンドに表示される可能性

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.task_processing_started": "Task processing started"
"messages.task_processing_started": "タスク処理を開始しました"

# コード修正
return {"message": t('messages.task_processing_started'), "task_id": task_id}
```

---

#### 15. Line 250: タスク未完了エラー
**現在のコード**:
```python
raise HTTPException(
    status_code=400,
    detail=f"タスクは完了していません（ステータス: {task.status}）"
)
```

**表示タイミング**: Excel出力時、タスクが未完了の場合
**影響**: HTTPエラーレスポンスとして返される

**英語対応方法**:
```python
# 翻訳キー追加（en.json / ja.json）
"messages.task_not_completed": "Task is not completed (status: {status})"
"messages.task_not_completed": "タスクは完了していません（ステータス: {status}）"

# コード修正
raise HTTPException(
    status_code=400,
    detail=t('messages.task_not_completed').replace('{status}', task.status)
)
```

---

## 📊 集計

| ファイル | 箇所数 | 内容 |
|---------|--------|------|
| chat_service.py | 5 | チャット調整関連メッセージ |
| input_service.py | 5 | ファイル読み込みエラーメッセージ |
| tasks.py | 5 | API関連メッセージ |
| **合計** | **15箇所** | - |

---

## 🔧 実装手順

### Step 1: 翻訳ファイルに追加（en.json / ja.json）

**追加する翻訳キー（15個）**:

#### chat_service.py用
```json
"messages.budget_cap_summary": "Total ${current} → ${new} (adjusted to cap ${cap} with factor {ratio})"
"messages.estimate_not_created": "Estimate has not been created yet. Please upload an Excel file and execute first."
"messages.direction_reduce": "reduction"
"messages.direction_increase": "increase"
"messages.proposal_generated": "We propose 3 {direction} options of approximately ${amount}.\n\nPlease select the most suitable option."
"messages.proposal_generation_failed": "Proposal generation failed. Please try the traditional adjustment method."
```

#### input_service.py用
```json
"messages.excel_min_columns": "Excel file must have at least 2 columns (deliverable name, description)."
"messages.excel_load_failed": "Failed to load Excel file: {error}"
"messages.csv_min_columns": "CSV file must have at least 2 columns (deliverable name, description)."
"messages.csv_load_failed": "Failed to load CSV file: {error}"
"messages.deliverable_parse_failed": "Failed to parse deliverable data: {error}"
```

#### tasks.py用
```json
"messages.invalid_file_type": "Only Excel (.xlsx, .xls) or CSV (.csv) files can be uploaded"
"messages.json_parse_failed": "Failed to parse deliverable data JSON"
"messages.file_or_data_required": "Please specify a file or deliverable data"
"messages.task_processing_started": "Task processing started"
"messages.task_not_completed": "Task is not completed (status: {status})"
```

### Step 2: 各ファイルでt()関数を使用

#### chat_service.py（5箇所修正）
1. Line 115: `t('messages.budget_cap_summary')`
2. Line 1056: `t('messages.estimate_not_created')`
3. Line 1114: `t('messages.direction_reduce')` / `t('messages.direction_increase')`
4. Line 1115: `t('messages.proposal_generated')`
5. Line 1155: `t('messages.proposal_generation_failed')`

#### input_service.py（5箇所修正）
- Line 18, 37, 48, 67, 90

#### tasks.py（5箇所修正）
- Line 88, 127, 136, 211, 250

### Step 3: テスト

1. **英語環境テスト**: `.env`でLANGUAGE=enに設定 → 全メッセージが英語で表示されるか確認
2. **日本語環境テスト**: `.env`でLANGUAGE=jaに設定 → 全メッセージが日本語で表示されるか確認
3. **エラーケーステスト**: 各エラーメッセージが正しく表示されるか確認

### Step 4: システム再起動

```bash
sudo systemctl restart estimator
```

---

## ⚠️ 重要な注意事項

1. **input_service.pyの対応**: `from app.core.i18n import t`のインポートが必要
2. **tasks.pyの対応**: すでに`from app.core.i18n import t`がインポート済み
3. **chat_service.pyの対応**: すでに`from app.core.i18n import t`がインポート済み
4. **{...}プレースホルダー**: `.replace('{key}', value)`で動的置換が必要
5. **通貨記号の対応**: `${amount}` vs `{amount}円`は翻訳ファイルで吸収

---

## 📝 備考

### 除外した箇所（ユーザーに表示されない）
- OpenAI APIに送信されるプロンプト（chat_service.py Line 710-749, 814, 886, 1228-1233）
- question_prompts.pyの全プロンプト指示文（OpenAI APIへの内部プロンプト）
- estimate_prompts.pyの全プロンプト指示文（OpenAI APIへの内部プロンプト）
- デバッグログ（print文等）

これらは**AIへの指示**であり、ユーザー画面には表示されないため、優先度を下げています。
ただし、将来的にはプロンプトも多言語化することで、AIの応答品質を向上させる可能性があります。

---

**作成者**: Claude Code
**最終更新**: 2025-10-24
