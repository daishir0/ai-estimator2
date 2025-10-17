# 英語化実装提案 (English Localization Proposal)

**プロジェクト**: AI見積りシステム (ai-estimator2)
**作成日**: 2025-10-17
**目的**: 設定で日本語/英語を切り替え可能にする完全国際化対応

---

## 📋 概要 (Overview)

このシステムを**環境変数で言語を切り替え**られるように改修します。

### 要件
1. **UI上の全テキスト**を多言語対応
2. **LLMとの対話プロンプト**を多言語対応
3. **設定で日本語/英語を切り替え**可能
4. **現在の日本語版**と完全に同じ機能を英語でも提供

---

## 🎯 実装方式の提案

### 方式: 多言語ファイルベース + 環境変数制御

#### 長所
- ✅ 翻訳の一元管理
- ✅ 簡単な言語追加（将来的に中国語・韓国語も対応可能）
- ✅ プログラムコードと翻訳の分離
- ✅ 翻訳の更新が容易

#### 短所
- ⚠️ 初回実装の工数がやや大きい
- ⚠️ ファイル数が増える

---

## 📂 ディレクトリ構成

```
backend/
├── app/
│   ├── locales/              # 新規作成
│   │   ├── __init__.py
│   │   ├── ja.json          # 日本語翻訳
│   │   └── en.json          # 英語翻訳
│   ├── core/
│   │   ├── config.py        # 修正: LANGUAGE設定追加
│   │   └── i18n.py          # 新規作成: 翻訳関数
│   ├── static/
│   │   ├── i18n.js          # 新規作成: フロントエンド翻訳
│   │   └── index.html       # 修正: 多言語対応
│   ├── services/
│   │   ├── question_service.py    # 修正: プロンプト多言語化
│   │   ├── estimator_service.py   # 修正: プロンプト多言語化
│   │   └── chat_service.py        # 修正: プロンプト多言語化
│   └── prompts/             # 新規作成
│       ├── __init__.py
│       ├── question_prompts.py    # 質問生成プロンプト
│       ├── estimate_prompts.py    # 見積りプロンプト
│       └── chat_prompts.py        # チャットプロンプト
```

---

## 🔧 実装詳細

### 1. 環境変数設定

**`.env` に追加**

```bash
# Language Setting (ja or en)
LANGUAGE=ja
```

**`backend/app/core/config.py` に追加**

```python
class Settings(BaseSettings):
    # 既存の設定...

    # Language setting
    LANGUAGE: str = "ja"  # Default: Japanese
```

---

### 2. 翻訳ファイル作成

#### `backend/app/locales/ja.json` (日本語)

```json
{
  "ui": {
    "app_title": "AI見積りシステム",
    "app_subtitle": "Excelからプロ品質の見積を自動生成",
    "step1_title": "1. 成果物データを入力",
    "step2_title": "2. 質問に回答",
    "step3_title": "3. 見積り結果",
    "tab_excel": "Excel",
    "tab_csv": "CSV",
    "tab_form": "Webフォーム",
    "button_create_task": "タスク作成",
    "button_submit_answers": "見積りを実行",
    "button_download": "Excelをダウンロード",
    "label_deliverable_name": "成果物名称",
    "label_deliverable_desc": "説明",
    "label_system_requirements": "システム要件（任意）",
    "placeholder_system_requirements": "例: Webシステム。最大同時100接続、AWS(ECS/RDS)、Salesforce連携など",
    "placeholder_deliverable_name": "例: 要件定義書",
    "placeholder_deliverable_desc": "例: システム全体の要件定義",
    "message_task_created": "タスクが作成されました",
    "message_estimate_completed": "見積りが完了しました",
    "message_estimate_failed": "見積り実行に失敗しました",
    "message_file_required": "ファイルを選択してください",
    "error_no_deliverables": "成果物を1件以上入力してください",
    "label_subtotal": "小計",
    "label_tax": "税額(10%)",
    "label_total": "総額",
    "label_person_days": "工数",
    "label_amount": "金額",
    "label_reasoning_breakdown": "工数内訳",
    "label_reasoning_notes": "根拠・備考",
    "button_expand_all": "全て開く",
    "button_collapse_all": "全て閉じる",
    "label_adjust_title": "見積り調整",
    "label_quick_adjust": "クイック見積調整（機械的適用）",
    "label_ai_adjust": "AI見積調整（自由入力）",
    "button_fit_budget": "上限予算に合わせる",
    "button_change_unit_cost": "単価を変更",
    "button_add_risk_buffer": "リスクバッファ追加",
    "button_reduce_scope": "機能を絞る",
    "button_send": "送信",
    "button_apply": "調整案を反映（Excel再出力）",
    "button_reset": "最初の見積内容に戻す",
    "placeholder_chat_input": "例: あと30万円ほど安くする案を教えて",
    "message_proposal_applied": "提案を適用しました！",
    "button_apply_proposal": "この案を適用する"
  },
  "prompts": {
    "question_system": "あなたは経験豊富なシステム開発プロジェクトマネージャーです。",
    "question_instruction": "以下の成果物とシステム要件を基に、見積り精度を向上させるための重要な質問を3つ生成してください。",
    "question_format": "質問1の内容\n質問2の内容\n質問3の内容",
    "estimate_system": "あなたは経験豊富なシステム開発プロジェクトマネージャーです。",
    "estimate_instruction": "以下の情報を基に、成果物の開発工数を見積もってください。",
    "estimate_unit": "人日",
    "estimate_breakdown_format": "- 要件定義: X.X人日\n- 設計: X.X人日\n- 実装: X.X人日\n- テスト: X.X人日\n- ドキュメント作成: X.X人日"
  },
  "defaults": {
    "question1": "想定しているユーザー数とアクセス頻度はどの程度ですか？",
    "question2": "システムの稼働環境（オンプレミス、クラウド等）はどちらを想定していますか？",
    "question3": "外部システムとの連携や既存システムとの統合は必要ですか？"
  },
  "messages": {
    "scope_reduce_no_keywords": "対象キーワードが指定されていません。",
    "scope_reduce_removed": "除外対象: {items}",
    "scope_reduce_none": "除外対象: なし",
    "fit_budget_no_change": "現在の総額は {current} 円で、上限 {cap} 円以下のため調整は不要です。",
    "fit_budget_adjusted": "総額 {current} 円 → {new} 円（上限 {cap} 円に合わせ係数 {ratio} を適用）",
    "unit_cost_changed": "単価を {cost} 円/人日に変更しました。",
    "risk_buffer_added": "リスクバッファ {percent}% を上乗せしました。",
    "ai_request_received": "ご要望を承知しました。以下の調整案を適用します。"
  }
}
```

#### `backend/app/locales/en.json` (英語)

```json
{
  "ui": {
    "app_title": "AI Estimator System",
    "app_subtitle": "Auto-generate professional estimates from Excel",
    "step1_title": "1. Input Deliverables",
    "step2_title": "2. Answer Questions",
    "step3_title": "3. Estimation Results",
    "tab_excel": "Excel",
    "tab_csv": "CSV",
    "tab_form": "Web Form",
    "button_create_task": "Create Task",
    "button_submit_answers": "Generate Estimate",
    "button_download": "Download Excel",
    "label_deliverable_name": "Deliverable Name",
    "label_deliverable_desc": "Description",
    "label_system_requirements": "System Requirements (Optional)",
    "placeholder_system_requirements": "e.g., Web system. Max 100 concurrent connections, AWS(ECS/RDS), Salesforce integration",
    "placeholder_deliverable_name": "e.g., Requirements Document",
    "placeholder_deliverable_desc": "e.g., Overall system requirements definition",
    "message_task_created": "Task created successfully",
    "message_estimate_completed": "Estimation completed",
    "message_estimate_failed": "Estimation failed",
    "message_file_required": "Please select a file",
    "error_no_deliverables": "Please input at least one deliverable",
    "label_subtotal": "Subtotal",
    "label_tax": "Tax(10%)",
    "label_total": "Total",
    "label_person_days": "Effort",
    "label_amount": "Amount",
    "label_reasoning_breakdown": "Effort Breakdown",
    "label_reasoning_notes": "Rationale & Notes",
    "button_expand_all": "Expand All",
    "button_collapse_all": "Collapse All",
    "label_adjust_title": "Estimate Adjustment",
    "label_quick_adjust": "Quick Adjust (Mechanical)",
    "label_ai_adjust": "AI Adjust (Free Input)",
    "button_fit_budget": "Fit to Budget",
    "button_change_unit_cost": "Change Unit Cost",
    "button_add_risk_buffer": "Add Risk Buffer",
    "button_reduce_scope": "Reduce Scope",
    "button_send": "Send",
    "button_apply": "Apply Adjustments (Re-generate Excel)",
    "button_reset": "Reset to Original",
    "placeholder_chat_input": "e.g., Please reduce the cost by about $3,000",
    "message_proposal_applied": "Proposal applied successfully!",
    "button_apply_proposal": "Apply This Proposal"
  },
  "prompts": {
    "question_system": "You are an experienced system development project manager.",
    "question_instruction": "Based on the following deliverables and system requirements, generate 3 important questions to improve estimation accuracy.",
    "question_format": "Question 1\nQuestion 2\nQuestion 3",
    "estimate_system": "You are an experienced system development project manager.",
    "estimate_instruction": "Based on the following information, estimate the development effort for the deliverable.",
    "estimate_unit": "person-days",
    "estimate_breakdown_format": "- Requirements: X.X person-days\n- Design: X.X person-days\n- Implementation: X.X person-days\n- Testing: X.X person-days\n- Documentation: X.X person-days"
  },
  "defaults": {
    "question1": "What is the estimated number of users and access frequency?",
    "question2": "What is the intended operating environment (on-premise, cloud, etc.)?",
    "question3": "Is integration with external systems or existing systems required?"
  },
  "messages": {
    "scope_reduce_no_keywords": "No keywords specified.",
    "scope_reduce_removed": "Removed items: {items}",
    "scope_reduce_none": "Removed items: none",
    "fit_budget_no_change": "Current total is {current}, which is already under the cap of {cap}. No adjustment needed.",
    "fit_budget_adjusted": "Total {current} → {new} (adjusted to cap {cap} with factor {ratio})",
    "unit_cost_changed": "Changed unit cost to {cost} per person-day.",
    "risk_buffer_added": "Added {percent}% risk buffer.",
    "ai_request_received": "Request received. Applying the following adjustments."
  }
}
```

---

### 3. バックエンド翻訳関数作成

#### `backend/app/core/i18n.py` (新規作成)

```python
"""多言語化対応"""
import json
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings

class I18n:
    def __init__(self, language: str = None):
        self.language = language or settings.LANGUAGE
        self.translations: Dict[str, Any] = {}
        self.load_translations()

    def load_translations(self):
        """翻訳ファイルを読み込む"""
        locale_dir = Path(__file__).parent.parent / "locales"
        locale_file = locale_dir / f"{self.language}.json"

        if not locale_file.exists():
            # デフォルト(日本語)にフォールバック
            locale_file = locale_dir / "ja.json"

        with open(locale_file, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

    def t(self, key: str, **kwargs) -> str:
        """
        翻訳を取得

        Args:
            key: 'ui.app_title' のようなドット区切りのキー
            **kwargs: プレースホルダー置換用の引数

        Returns:
            翻訳されたテキスト

        Examples:
            t('ui.app_title') => 'AI見積りシステム' or 'AI Estimator System'
            t('messages.fit_budget_adjusted', current=100, new=90, cap=95, ratio=0.9)
        """
        keys = key.split('.')
        value = self.translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return f"[Missing: {key}]"

        # プレースホルダー置換
        if isinstance(value, str) and kwargs:
            for k, v in kwargs.items():
                value = value.replace(f"{{{k}}}", str(v))

        return value

    def get_all(self, prefix: str) -> Dict[str, Any]:
        """特定のプレフィックスですべての翻訳を取得"""
        keys = prefix.split('.')
        value = self.translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return {}

        return value if isinstance(value, dict) else {}

# グローバルインスタンス
i18n = I18n()

def get_i18n() -> I18n:
    """依存性注入用"""
    return i18n

def t(key: str, **kwargs) -> str:
    """ショートカット関数"""
    return i18n.t(key, **kwargs)
```

---

### 4. フロントエンド翻訳システム

#### `backend/app/static/i18n.js` (新規作成)

```javascript
// 翻訳データ（サーバーから取得）
let translations = {};
let currentLanguage = 'ja';

// 翻訳データをサーバーから取得
async function loadTranslations() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/translations`);
    if (res.ok) {
      const data = await res.json();
      translations = data.translations || {};
      currentLanguage = data.language || 'ja';

      // DOM更新
      translatePage();
    }
  } catch (e) {
    console.error('翻訳データの読み込みに失敗しました:', e);
  }
}

// 翻訳関数
function t(key, params = {}) {
  const keys = key.split('.');
  let value = translations;

  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return `[Missing: ${key}]`;
    }
  }

  // プレースホルダー置換
  if (typeof value === 'string' && Object.keys(params).length > 0) {
    for (const [k, v] of Object.entries(params)) {
      value = value.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
  }

  return value;
}

// ページ全体を翻訳
function translatePage() {
  // data-i18n属性を持つ要素を翻訳
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });

  // data-i18n-placeholder属性を持つ要素のプレースホルダーを翻訳
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(key);
  });

  // タイトルを翻訳
  document.title = t('ui.app_title');

  // HTML lang属性を更新
  document.documentElement.lang = currentLanguage;
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
  loadTranslations();
});
```

---

### 5. API エンドポイント追加

#### `backend/app/api/v1/tasks.py` に追加

```python
from app.core.i18n import get_i18n

@router.get("/translations")
async def get_translations():
    """フロントエンド用の翻訳データを返す"""
    i18n = get_i18n()
    return {
        "language": i18n.language,
        "translations": i18n.translations
    }
```

---

### 6. サービス層の修正

#### `backend/app/prompts/question_prompts.py` (新規作成)

```python
"""質問生成プロンプト"""
from app.core.i18n import t

def get_question_generation_prompt(deliverables_text: str, system_requirements: str) -> str:
    """質問生成プロンプトを生成"""
    return f"""
{t('prompts.question_system')}
{t('prompts.question_instruction')}

【{t('ui.label_deliverable_name')}】
{deliverables_text}

【{t('ui.label_system_requirements')}】
{system_requirements}

【指示】
1. {t('prompts.question_instruction')}
2. 技術的な複雑さ、スケジュール、リソースに関する質問を含めてください
3. 具体的で答えやすい質問にしてください
4. 各質問は一行で簡潔に記載してください
5. 質問番号は付けず、質問文のみを出力してください

出力形式：
{t('prompts.question_format')}
"""

def get_system_prompt() -> str:
    """システムプロンプトを取得"""
    return t('prompts.question_system')
```

#### `backend/app/prompts/estimate_prompts.py` (新規作成)

```python
"""見積りプロンプト"""
from app.core.i18n import t

def get_estimate_prompt(deliverable: dict, system_requirements: str, qa_text: str) -> str:
    """見積りプロンプトを生成"""
    unit = t('prompts.estimate_unit')

    return f"""
{t('prompts.estimate_system')}
{t('prompts.estimate_instruction')}

【成果物情報】
{t('ui.label_deliverable_name')}: {deliverable['name']}
{t('ui.label_deliverable_desc')}: {deliverable['description']}

【{t('ui.label_system_requirements')}】
{system_requirements}

【追加情報】
{qa_text}

【厳守事項】
- 単位は必ず「{unit}」を使用し、数字の桁を間違えないこと（例: 4.5{unit}を45と書かない）
- reasoning_breakdown内のすべての数量表記も「{unit}」とし、小数1桁を維持する

【出力形式】
次のJSONのみをコードブロックなしで返す：
{{
  "person_days": 小数1桁の数値（例: 4.5）,
  "reasoning_breakdown": "工数内訳（Markdown可）。工程別の{unit}内訳を箇条書きで記載。",
  "reasoning_notes": "根拠・備考（Markdown可）。見積りの前提条件、リスク、補足説明など。"
}}

【reasoning_breakdown のフォーマット】
以下の統一フォーマットで記載してください：
{t('prompts.estimate_breakdown_format')}

【見積り範囲】
- 設計・実装・テスト・ドキュメント作成を含める
- 成果物の複雑さを考慮した現実的な工数
- reasoning_breakdownには工程別の数値内訳を統一フォーマットで記載
- reasoning_notesには前提条件やリスク、注意点を記載
"""

def get_system_prompt() -> str:
    """システムプロンプトを取得"""
    return t('prompts.estimate_system')
```

#### `backend/app/services/question_service.py` の修正

```python
"""質問生成サービス"""
import openai
from typing import List, Dict
from app.core.config import settings
from app.prompts.question_prompts import get_question_generation_prompt, get_system_prompt
from app.core.i18n import t

class QuestionService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate_questions(
        self, deliverables: List[Dict[str, str]], system_requirements: str
    ) -> List[str]:
        """成果物とシステム要件から、見積り精度向上のための3つの質問を生成する"""

        deliverable_list = "\n".join(
            [f"- {item['name']}: {item['description']}" for item in deliverables]
        )

        prompt = get_question_generation_prompt(deliverable_list, system_requirements)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

            if len(questions) < 3:
                questions.extend(self._get_default_questions()[len(questions) :])

            return questions[:3]

        except Exception as e:
            print(f"AI質問生成でエラーが発生しました: {e}")
            return self._get_default_questions()

    def _get_default_questions(self) -> List[str]:
        """デフォルトの質問を返す"""
        return [
            t('defaults.question1'),
            t('defaults.question2'),
            t('defaults.question3'),
        ]
```

---

### 7. HTMLの修正 (`backend/app/static/index.html`)

**変更箇所の例**:

```html
<!-- Before -->
<title>AI見積りシステム Web</title>

<!-- After -->
<title data-i18n="ui.app_title">AI見積りシステム Web</title>
```

```html
<!-- Before -->
<div class="text-slate-900 font-semibold">AI見積りシステム</div>

<!-- After -->
<div class="text-slate-900 font-semibold" data-i18n="ui.app_title">AI見積りシステム</div>
```

```html
<!-- Before -->
<input id="system_requirements" placeholder="例: Webシステム。最大同時100接続、AWS(ECS/RDS)、Salesforce連携など" />

<!-- After -->
<input id="system_requirements" data-i18n-placeholder="ui.placeholder_system_requirements" placeholder="例: Webシステム..." />
```

**i18n.js の読み込み**:

```html
<head>
  <!-- 既存のスクリプト -->
  <script src="/static/i18n.js"></script>
</head>
```

---

## 📝 実装手順

### Phase 1: 基盤整備（1-2日）

1. **翻訳ファイル作成**
   - [ ] `backend/app/locales/ja.json` 作成
   - [ ] `backend/app/locales/en.json` 作成
   - [ ] すべてのUI文言を翻訳

2. **バックエンド翻訳システム**
   - [ ] `backend/app/core/i18n.py` 作成
   - [ ] `backend/app/core/config.py` に `LANGUAGE` 設定追加
   - [ ] `.env.sample` に `LANGUAGE=ja` 追加

3. **フロントエンド翻訳システム**
   - [ ] `backend/app/static/i18n.js` 作成
   - [ ] API エンドポイント `/api/v1/translations` 追加

### Phase 2: プロンプト多言語化（1-2日）

4. **プロンプトファイル作成**
   - [ ] `backend/app/prompts/question_prompts.py` 作成
   - [ ] `backend/app/prompts/estimate_prompts.py` 作成
   - [ ] `backend/app/prompts/chat_prompts.py` 作成

5. **サービス層修正**
   - [ ] `question_service.py` 修正
   - [ ] `estimator_service.py` 修正
   - [ ] `chat_service.py` 修正

### Phase 3: UI多言語化（2-3日）

6. **HTML修正**
   - [ ] すべてのテキストに `data-i18n` 属性追加
   - [ ] すべての `placeholder` に `data-i18n-placeholder` 属性追加
   - [ ] JavaScript内のハードコードされたメッセージを翻訳関数に変更

### Phase 4: テスト・検証（1日）

7. **動作確認**
   - [ ] 日本語モードでの動作確認
   - [ ] 英語モードでの動作確認
   - [ ] UI表示の確認
   - [ ] LLM応答の確認
   - [ ] エラーメッセージの確認

---

## 🧪 動作確認方法

### 日本語モード

```bash
# .env
LANGUAGE=ja

# 起動
cd backend
uvicorn app.main:app --reload
```

→ http://localhost:8000/ui にアクセス
→ すべて日本語で表示されることを確認

### 英語モード

```bash
# .env
LANGUAGE=en

# 再起動
uvicorn app.main:app --reload
```

→ http://localhost:8000/ui にアクセス
→ すべて英語で表示されることを確認

---

## 📋 翻訳が必要な箇所のチェックリスト

### UI (index.html)
- [ ] ヘッダー
- [ ] タイトル・サブタイトル
- [ ] ステップタイトル（1,2,3）
- [ ] タブラベル（Excel/CSV/Webフォーム）
- [ ] ボタンラベル（全て）
- [ ] ラベル（全て）
- [ ] プレースホルダー（全て）
- [ ] エラーメッセージ
- [ ] トースト通知
- [ ] 確認ダイアログ

### LLMプロンプト
- [ ] 質問生成プロンプト
- [ ] 見積りプロンプト
- [ ] チャットプロンプト（調整提案）
- [ ] システムプロンプト

### デフォルト値
- [ ] デフォルト質問（3つ）
- [ ] デフォルト見積り理由

### メッセージ
- [ ] 調整メッセージ
- [ ] エラーメッセージ
- [ ] 成功メッセージ

---

## 🎨 UI表示例（英語版）

### ヘッダー
```
AI Estimator System
Auto-generate professional estimates from Excel
```

### Step 1
```
1. Input Deliverables

Tab: [Excel] [CSV] [Web Form]

Excel File (.xlsx/.xls)
[Choose File]
Download Sample Excel

System Requirements (Optional)
[Textbox: e.g., Web system. Max 100 concurrent connections, AWS(ECS/RDS), Salesforce integration]

[Create Task]
```

### Step 2
```
2. Answer Questions

Question 1
What is the estimated number of users and access frequency?
Answer: [Textbox]

[Generate Estimate]
```

### Step 3
```
3. Estimation Results
[Download Excel]

Subtotal: 1,200,000
Tax(10%): 120,000
Total: 1,320,000

[Chart]

Estimate Adjustment

Quick Adjust (Mechanical):
[Input: Budget Cap] [Fit to Budget]
[Input: Unit Cost] [Change Unit Cost]

AI Adjust (Free Input):
[Input: e.g., Please reduce the cost by about $3,000] [Send]
```

---

## 💡 追加機能の提案（オプション）

### 1. ブラウザ言語自動検出

```javascript
// i18n.js に追加
function detectBrowserLanguage() {
  const browserLang = navigator.language || navigator.userLanguage;
  if (browserLang.startsWith('ja')) {
    return 'ja';
  } else if (browserLang.startsWith('en')) {
    return 'en';
  }
  return 'ja'; // デフォルト
}

// サーバー設定が優先、なければブラウザ言語を使用
```

### 2. 言語切り替えボタン

```html
<!-- ヘッダーに追加 -->
<div class="language-switcher">
  <button onclick="switchLanguage('ja')">日本語</button>
  <button onclick="switchLanguage('en')">English</button>
</div>
```

```javascript
async function switchLanguage(lang) {
  // サーバーに言語変更リクエスト送信
  await fetch(`${API_BASE}/api/v1/language`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: lang })
  });

  // ページリロード
  location.reload();
}
```

---

## 📊 見積もり工数

| フェーズ | 内容 | 工数 |
|---------|------|------|
| Phase 1 | 基盤整備 | 1-2日 |
| Phase 2 | プロンプト多言語化 | 1-2日 |
| Phase 3 | UI多言語化 | 2-3日 |
| Phase 4 | テスト・検証 | 1日 |
| **合計** | | **5-8日** |

---

## ⚠️ 注意事項

### 1. 通貨表示
- 日本語: 「1,200,000円」
- 英語: 「¥1,200,000」または「JPY 1,200,000」

実装では、`toLocaleString()`を使用することで自動対応可能：

```javascript
// 日本語
amount.toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })
// => ¥1,200,000

// 英語
amount.toLocaleString('en-US', { style: 'currency', currency: 'JPY' })
// => ¥1,200,000
```

### 2. 日付表示
- 日本語: 「2025年10月17日」
- 英語: 「October 17, 2025」

### 3. 単位
- 日本語: 「人日」
- 英語: 「person-days」または「man-days」

### 4. LLMの言語能力
- GPT-4o-miniは日英両言語に対応
- プロンプトを英語にすれば、英語で回答を生成可能
- 精度は日本語とほぼ同等

---

## 🔄 既存機能への影響

### ✅ 影響なし
- データベース構造
- API エンドポイント（翻訳API以外）
- ビジネスロジック
- Excel生成機能

### ⚠️ 要修正
- UI テキスト（全て）
- LLM プロンプト（全て）
- エラーメッセージ
- ログ出力（オプション）

---

## 📚 参考実装（他プロジェクト）

### Vue I18n方式（参考）
```javascript
// 類似の実装例
const i18n = {
  ja: { message: { hello: 'こんにちは' } },
  en: { message: { hello: 'Hello' } }
};

function t(key) {
  return key.split('.').reduce((o, k) => o[k], i18n[currentLang]);
}
```

---

## 🎯 成功基準

### 最低限の成功基準
- [ ] 環境変数でja/enを切り替え可能
- [ ] UIが完全に多言語化されている
- [ ] LLMが適切な言語で応答する
- [ ] 日本語モードが現在と同じ動作をする

### 理想的な成功基準
- [ ] ブラウザ言語自動検出
- [ ] 言語切り替えボタン
- [ ] 将来の言語追加が容易
- [ ] 翻訳ファイルの保守性が高い

---

**作成者**: Claude (AI Assistant)
**作成日**: 2025-10-17
**バージョン**: 1.0
