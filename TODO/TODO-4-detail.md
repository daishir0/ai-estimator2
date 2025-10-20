# TODO-4: 安全ポリシー・拒否方針策定

## 📋 概要
- **目的**: AI見積りシステムの安全性を確保するため、安全ポリシーと拒否方針を策定し、システムプロンプトに組み込む
- **期間**: Day 7
- **優先度**: 🔴 最高
- **依存関係**: TODO-2（Guardrails実装）、TODO-3（セキュリティリスク対応）

## 🎯 達成基準
- [ ] 安全ポリシー文書作成完了（ja/en）
- [ ] 拒否方針文書作成完了（ja/en）
- [ ] システムプロンプトへの安全ガイドライン組み込み完了
- [ ] SafetyService実装完了
- [ ] 拒否ハンドラー実装・テスト完了
- [ ] 多言語対応（ja/en）
- [ ] ドキュメントレビュー完了

---

## 📐 計画

### 1. 安全ポリシーの策定

#### 1.1 対象範囲

AI見積りシステムにおいて、以下の安全性を確保する：

1. **ユーザー入力の安全性**
   - 有害なコンテンツの検出・拒否
   - プロンプトインジェクション攻撃の防止
   - PII情報の保護

2. **LLM出力の安全性**
   - 不適切なコンテンツの検出・修正
   - 誤情報の防止
   - PII情報の漏洩防止

3. **システムの安全性**
   - サービス拒否攻撃の防止
   - コスト管理
   - エラーハンドリング

#### 1.2 ポリシー文書構成

**docs/safety/SAFETY_POLICY.md** (日本語版)

```markdown
# AI見積りシステム 安全ポリシー

## 1. 概要

このポリシーは、AI見積りシステムの安全で責任ある運用を確保するためのガイドラインです。

## 2. 基本原則

### 2.1 誠実性
- 正確で根拠のある見積りを提供
- 不確実性がある場合は明示
- 誤解を招く表現を避ける

### 2.2 透明性
- AI による生成である旨を明示
- 見積り根拠を提供
- 制限事項を説明

### 2.3 プライバシー保護
- PII情報を取得・保存・利用しない
- ユーザーデータは見積り目的のみに使用
- 適切な期間後にデータを削除

### 2.4 安全性
- 有害なコンテンツを生成・受け入れない
- セキュリティベストプラクティスに従う
- 継続的な監視と改善

## 3. 禁止事項

システムは以下のコンテンツを生成・受け入れません：

### 3.1 有害なコンテンツ
- 違法、暴力的、脅迫的な内容
- 差別的、中傷的な内容
- 性的に露骨な内容
- ハラスメント的な内容

### 3.2 不正な操作
- 不当に高額または低額な見積り
- 根拠のない金額操作
- 意図的な誤情報

### 3.3 プライバシー侵害
- 個人情報（名前、メールアドレス、電話番号等）の要求
- 機密情報の漏洩
- トラッキング・監視

## 4. 拒否基準

システムは以下の場合、処理を自動的に拒否します：

### 4.1 入力拒否
- 毒性スコア 0.8以上の言語
- プロンプトインジェクションパターン検出
- 入力長 10,000文字超過
- 不正なファイル形式
- ファイルサイズ制限超過（10MB）

### 4.2 出力拒否
- PII情報を含む出力
- 毒性スコア 0.8以上の出力
- スキーマ検証失敗
- ビジネスルール違反（工数範囲外等）

## 5. エスカレーション手順

### 5.1 拒否時の対応
1. ユーザーに明確なエラーメッセージを返す
2. 拒否理由をログに記録
3. 繰り返し違反の場合、管理者に通知

### 5.2 エラーメッセージ
- 技術的詳細は含めない
- 改善方法を提示
- サポート連絡先を案内

## 6. 監視とレビュー

### 6.1 継続的監視
- 拒否された入力/出力の定期レビュー
- 誤検知の分析と改善
- ポリシーの定期更新（四半期ごと）

### 6.2 インシデント対応
- セキュリティインシデント発生時の手順
- 影響範囲の評価
- 再発防止策の策定

## 7. コンプライアンス

- GDPR、個人情報保護法等のデータ保護規制に準拠
- OWASP LLM Top 10に基づくセキュリティ対策
- 定期的なセキュリティ監査

---

**発効日**: 2025-10-18
**改訂履歴**:
- 2025-10-18: 初版作成
```

### 2. システムプロンプトへの組み込み

#### 2.1 安全ガイドラインの定義

**app/prompts/safety_guidelines.py** (新規作成)

```python
from app.core.i18n import t

def get_safety_guidelines() -> str:
    """安全ガイドラインを取得（多言語対応）"""
    return t('prompts.safety_guidelines')
```

**翻訳ファイル更新** (app/locales/ja.json)

```json
{
  "prompts": {
    "safety_guidelines": "\n## 安全ガイドライン\n\n以下の原則に従ってください：\n1. 正確で誠実な見積りを提供する\n2. 不確実性がある場合は明示する\n3. 不適切または違法な要求には応じない\n4. 個人情報を含まない\n5. 専門的で中立的なトーンを維持する\n\n禁止事項：\n- 根拠のない金額の提示\n- 個人情報の要求\n- 差別的または攻撃的な言葉の使用\n"
  }
}
```

#### 2.2 プロンプト更新

**app/prompts/question_prompts.py** (変更)

```python
from app.prompts.safety_guidelines import get_safety_guidelines

def get_system_prompt() -> str:
    """質問生成システムプロンプト（安全ガイドライン付き）"""
    base = t('prompts.question_system')
    language_instruction = t('prompts.language_instruction')
    safety = get_safety_guidelines()

    return f"{base}\n\n{safety}\n\n{language_instruction}"
```

**app/prompts/estimate_prompts.py** (同様に変更)

**app/prompts/chat_prompts.py** (同様に変更)

### 3. SafetyService実装

#### 3.1 SafetyService (app/services/safety_service.py)

```python
from typing import Tuple
import logging
from fastapi import HTTPException
from app.services.guardrails_service import GuardrailsService
from app.services.security_service import SecurityService
from app.core.i18n import t

logger = logging.getLogger(__name__)

class SafetyService:
    """安全性チェックと拒否ハンドリング"""

    def __init__(self):
        self.guardrails = GuardrailsService()
        self.security = SecurityService()

    def check_input_safety(self, content: str, content_type: str = "input") -> Tuple[bool, str]:
        """入力の安全性チェック

        Returns:
            (is_safe: bool, message: str)
        """
        try:
            # 1. セキュリティチェック（プロンプトインジェクション）
            self.security.check_prompt_injection(content)

            # 2. Guardrailsチェック（有害言語、PII、長さ）
            self.guardrails.validate_input(content)

            return True, "OK"

        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Safety check failed ({content_type}): {error_msg}")
            return False, error_msg

    def check_output_safety(self, content: str) -> Tuple[bool, str]:
        """出力の安全性チェック"""
        try:
            self.guardrails.validate_output(content)
            return True, "OK"
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Output safety check failed: {error_msg}")
            return False, error_msg

    def handle_rejection(self, reason: str, content_type: str = "input") -> None:
        """拒否時の処理（例外を投げる）"""
        # ログ記録
        logger.warning(f"Request rejected ({content_type}): {reason}")

        # ユーザーへのエラーメッセージ
        user_message = self._get_user_friendly_message(reason)

        raise HTTPException(
            status_code=400,
            detail=user_message
        )

    def _get_user_friendly_message(self, reason: str) -> str:
        """ユーザー向けエラーメッセージ生成"""
        if "prompt_injection" in reason.lower():
            return t('messages.safety_prompt_injection')
        elif "toxic" in reason.lower():
            return t('messages.safety_toxic_content')
        elif "pii" in reason.lower():
            return t('messages.safety_pii_detected')
        elif "length" in reason.lower():
            return t('messages.safety_length_exceeded')
        else:
            return t('messages.safety_general_rejection')
```

#### 3.2 API統合 (app/api/v1/tasks.py)

```python
from app.services.safety_service import SafetyService

safety_service = SafetyService()

@router.post("/tasks")
async def create_task(...):
    # システム要件の安全性チェック
    if system_requirements:
        is_safe, message = safety_service.check_input_safety(
            system_requirements,
            content_type="system_requirements"
        )
        if not is_safe:
            safety_service.handle_rejection(message, "system_requirements")
    # ... 既存処理 ...

@router.post("/tasks/{task_id}/answers")
async def submit_answers(...):
    # 各回答の安全性チェック
    for key, value in answers.items():
        is_safe, message = safety_service.check_input_safety(value, f"answer_{key}")
        if not is_safe:
            safety_service.handle_rejection(message, f"answer_{key}")
    # ... 既存処理 ...
```

### 4. 多言語対応

**翻訳ファイル更新**

**app/locales/ja.json**
```json
{
  "messages": {
    "safety_prompt_injection": "不正な入力が検出されました。入力内容を確認してください。",
    "safety_toxic_content": "不適切な内容が検出されました。適切な表現に修正してください。",
    "safety_pii_detected": "個人情報が含まれています。個人情報を削除してください。",
    "safety_length_exceeded": "入力が長すぎます。10,000文字以内にしてください。",
    "safety_general_rejection": "入力が安全基準を満たしていません。内容を見直してください。"
  }
}
```

**app/locales/en.json** (同様に英語翻訳追加)

### 5. 技術スタック

- **Python logging**: ログ記録
- **FastAPI HTTPException**: エラーハンドリング
- **Markdown**: ドキュメント記述

### 6. 影響範囲

**新規作成ファイル**
- `docs/safety/SAFETY_POLICY.md` (ja)
- `docs/safety/SAFETY_POLICY_EN.md` (en)
- `app/prompts/safety_guidelines.py`
- `app/services/safety_service.py`

**変更ファイル**
- `app/prompts/question_prompts.py`
- `app/prompts/estimate_prompts.py`
- `app/prompts/chat_prompts.py`
- `app/api/v1/tasks.py`
- `app/locales/ja.json`
- `app/locales/en.json`

**テストファイル追加**
- `backend/tests/unit/test_safety_service.py`
- `backend/tests/integration/test_safety_integration.py`

### 7. リスクと対策

#### リスク1: 過度な拒否（誤検知）
- **対策**: しきい値調整、ホワイトリスト機能、ユーザーフィードバック収集

#### リスク2: ポリシーの形骸化
- **対策**: 定期レビュー（四半期ごと）、実際の拒否ケース分析

#### リスク3: 多言語対応の不整合
- **対策**: 翻訳レビュー、両言語でのテスト実施

### 8. スケジュール

**Day 7**:
- 安全ポリシー文書作成（ja/en）
- 安全ガイドライン定義・翻訳追加
- システムプロンプト更新
- SafetyService実装
- API統合
- テスト実装
- ドキュメントレビュー

---

## 🔧 実施内容（実績）

### Day 7: [日付]
#### 実施作業
- [ ] 作業内容（実装時に記録）

#### 作成ファイル
- ファイル一覧（実装時に記録）

#### 確認・テスト
- [ ] テスト結果（実装時に記録）

#### 課題・気づき
- 課題・気づき（実装時に記録）

---

## 📊 実績

### 達成した成果
- 成果内容（完了時にまとめ）

### 拒否ケースの分析
- 拒否パターン（完了時にまとめ）

### 学び
- 学んだこと（完了時にまとめ）

---

## ✅ 完了チェックリスト
- [ ] 安全ポリシー文書完成（ja/en）
- [ ] システムプロンプトに安全ガイドライン組み込み
- [ ] SafetyService実装完了
- [ ] 拒否ハンドラー動作確認
- [ ] 多言語対応確認（ja/en）
- [ ] テスト実装完了
- [ ] ドキュメントレビュー完了

## 📚 参考資料
- todo.md (334-428行目): TODO-4詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/35_ai-that-doesnt-harm-principles-of-safety-and-alignment-aaidc-week9-lesson4.md`
- OpenAI Safety Best Practices: https://platform.openai.com/docs/guides/safety-best-practices

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-18
**担当**: Claude Code
**ステータス**: 計画完了
