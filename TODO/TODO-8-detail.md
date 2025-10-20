# TODO-8: データプライバシー対応（基本）

## 📋 概要
- **目的**: GDPR等のデータ保護規制に準拠するため、プライバシーポリシー策定とPII対策を実装する
- **期間**: Day 18-19
- **優先度**: 🔴 最高
- **依存関係**: TODO-2（Guardrails: PII検出）

## 🎯 達成基準
- [ ] プライバシーポリシー作成完了（ja/en）
- [ ] PII検出・マスキング実装完了
- [ ] データ削除API実装完了
- [ ] データ保持期間設定実装完了
- [ ] GDPRチェックリスト作成完了（ja/en）
- [ ] 多言語対応確認（ja/en）
- [ ] ドキュメント更新完了

---

## 📐 計画

### 1. データプライバシーポリシー策定

#### 1.1 プライバシーポリシー文書 (docs/privacy/PRIVACY_POLICY.md)

**目次**:
1. データ収集・利用方針
2. データ保管期間
3. 第三者提供
4. ユーザーの権利
5. GDPR対応
6. セキュリティ対策
7. お問い合わせ

**主要内容**:
```markdown
# プライバシーポリシー

## 1. データ収集・利用方針

### 収集するデータ

#### 入力データ
- 成果物名称
- 成果物説明
- システム要件
- 質問への回答

#### システムログ
- APIアクセスログ（リクエストID、エンドポイント、レスポンスタイム）
- エラーログ（エラー種別、発生時刻）
- パフォーマンスメトリクス（処理時間、OpenAI API使用状況）

### データ利用目的
1. プロジェクト見積りの生成
2. サービス品質の向上
3. エラー分析と改善
4. システム監視と運用

### 収集しないデータ
- 個人を特定できる情報（氏名、住所、電話番号、メールアドレス）
- 機密情報（クレジットカード情報、パスワード）
- トラッキングCookie

## 2. データ保管期間

| データ種別 | 保管期間 | 削除方法 |
|-----------|---------|---------|
| 見積りタスクデータ | 30日間 | 自動削除またはユーザー削除API |
| システムログ | 90日間 | 自動削除（ログローテーション） |
| メトリクス | 30日間 | 自動削除 |

## 3. 第三者提供

### OpenAI API
- **提供目的**: 見積り生成、質問生成、調整提案
- **提供データ**: 成果物名称、説明、システム要件、質問回答
- **PII対策**: PII検出・マスキング機能により、個人情報を除外
- **データ保持**: OpenAIのデータ使用ポリシーに準拠

### その他の第三者
- データを第三者に提供することはありません

## 4. ユーザーの権利

### アクセス権
- 自身の見積りデータにアクセス可能（GET /api/v1/tasks/{task_id}）

### 削除権
- 自身の見積りデータを削除可能（DELETE /api/v1/tasks/{task_id}）

### ポータビリティ権
- 見積りデータをExcel形式でダウンロード可能

## 5. GDPR対応

### 最小化原則
- 見積り生成に必要最小限のデータのみ収集
- 不要になったデータは自動削除

### 同意
- サービス利用開始時にプライバシーポリシーへの同意取得
- データ処理内容の明示

### 透明性
- データ利用目的の明示
- 第三者提供先（OpenAI）の明示

### セキュリティ
- 環境変数によるAPIキー管理
- HTTPS通信（本番環境）
- アクセスログ記録
- PII検出・マスキング

## 6. セキュリティ対策

- SSL/TLS暗号化通信（HTTPS）
- APIキーの環境変数管理
- 入力検証（Guardrails）
- プロンプトインジェクション対策
- ログからのPII除外

## 7. お問い合わせ

プライバシーに関するお問い合わせ：
- メール: privacy@example.com
- 対応時間: 平日 9:00-17:00（日本時間）

---

**発効日**: 2025-10-18
**改訂履歴**:
- 2025-10-18: 初版作成
```

### 2. PII対策実装

#### 2.1 PrivacyService (app/services/privacy_service.py)

```python
import re
from typing import Dict, List
from app.core.i18n import t

class PrivacyService:
    """プライバシー保護サービス"""

    # PII検出パターン
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone_jp": r'\b0\d{1,4}-\d{1,4}-\d{4}\b',  # 日本の電話番号
        "phone_intl": r'\b\+\d{1,3}-\d{1,4}-\d{1,4}-\d{4}\b',  # 国際電話番号
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',  # 米国SSN
        "my_number": r'\b\d{4}-\d{4}-\d{4}\b'  # 日本マイナンバー
    }

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """PII検出"""
        if not text:
            return {}

        detected = {}
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected[pii_type] = matches

        return detected

    def mask_pii(self, text: str) -> str:
        """PII マスキング"""
        if not text:
            return text

        for pii_type, pattern in self.PII_PATTERNS.items():
            text = re.sub(pattern, f"[{pii_type.upper()}_MASKED]", text, flags=re.IGNORECASE)

        return text

    def check_pii_compliance(self, text: str) -> tuple[bool, str]:
        """PII コンプライアンスチェック

        Returns:
            (is_compliant: bool, message: str)
        """
        detected = self.detect_pii(text)

        if detected:
            pii_types = ", ".join(detected.keys())
            return False, f"{t('messages.pii_detected')}: {pii_types}"

        return True, "OK"
```

#### 2.2 データ削除API (app/api/v1/tasks.py)

```python
from app.services.privacy_service import PrivacyService

privacy_service = PrivacyService()

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """タスクとすべての関連データを削除（GDPR対応）"""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail=t('messages.task_not_found'))

    # 関連データ削除
    db.query(Deliverable).filter(Deliverable.task_id == task_id).delete()
    db.query(QAPair).filter(QAPair.task_id == task_id).delete()
    db.query(Estimate).filter(Estimate.task_id == task_id).delete()
    db.query(Message).filter(Message.task_id == task_id).delete()

    # Excelファイル削除（存在する場合）
    if task.excel_file_path and os.path.exists(task.excel_file_path):
        os.remove(task.excel_file_path)

    if task.result_file_path and os.path.exists(task.result_file_path):
        os.remove(task.result_file_path)

    # タスク削除
    db.delete(task)
    db.commit()

    logger.info(f"Task {task_id} and all related data deleted (GDPR compliance)")

    return {"message": t('messages.task_deleted_successfully')}

@router.get("/tasks/{task_id}/privacy")
async def get_task_privacy_info(task_id: str, db: Session = Depends(get_db)):
    """タスクのプライバシー情報を取得"""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail=t('messages.task_not_found'))

    # データ保持期間計算
    from datetime import datetime, timedelta
    created_at = task.created_at
    retention_days = 30
    deletion_date = created_at + timedelta(days=retention_days)
    days_remaining = (deletion_date - datetime.now()).days

    return {
        "task_id": task_id,
        "created_at": created_at.isoformat(),
        "retention_days": retention_days,
        "auto_deletion_date": deletion_date.isoformat(),
        "days_remaining": max(0, days_remaining),
        "can_delete": True
    }
```

#### 2.3 自動データ削除（バッチ処理）

**app/tasks/cleanup.py** (新規作成)

```python
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.task import Task
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def cleanup_old_tasks():
    """30日以上経過したタスクを自動削除"""
    db: Session = SessionLocal()

    try:
        # 30日前の日時
        cutoff_date = datetime.now() - timedelta(days=30)

        # 古いタスクを取得
        old_tasks = db.query(Task).filter(Task.created_at < cutoff_date).all()

        deleted_count = 0
        for task in old_tasks:
            # タスクと関連データを削除
            # ... （DELETE APIと同じロジック）
            deleted_count += 1

        db.commit()

        logger.info(f"Auto cleanup: {deleted_count} tasks deleted")

    except Exception as e:
        db.rollback()
        logger.error(f"Auto cleanup failed: {e}")

    finally:
        db.close()
```

### 3. GDPRチェックリスト (docs/privacy/GDPR_CHECKLIST.md)

**目次**:
1. データ収集
2. データ処理
3. データ保管
4. ユーザー権利
5. セキュリティ
6. 文書化

### 4. 多言語対応

**翻訳追加** (app/locales/ja.json):
```json
{
  "messages": {
    "task_not_found": "タスクが見つかりません。",
    "task_deleted_successfully": "タスクが正常に削除されました。"
  }
}
```

### 5. 技術スタック

- **Python re**: 正規表現（PII検出）
- **SQLAlchemy**: データ削除
- **datetime**: データ保持期間管理

### 6. 影響範囲

**新規作成ファイル**
- `app/services/privacy_service.py`
- `app/tasks/cleanup.py`
- `docs/privacy/PRIVACY_POLICY.md` (ja/en)
- `docs/privacy/GDPR_CHECKLIST.md` (ja/en)

**変更ファイル**
- `app/api/v1/tasks.py` (DELETE API追加、プライバシー情報API追加)
- `app/locales/ja.json`
- `app/locales/en.json`

**テストファイル追加**
- `backend/tests/unit/test_privacy_service.py`
- `backend/tests/integration/test_data_deletion.py`

### 7. リスクと対策

#### リスク1: PII検出漏れ
- **対策**: パターン追加、定期レビュー

#### リスク2: データ削除の不完全性
- **対策**: カスケード削除、削除確認テスト

#### リスク3: 法規制の変更
- **対策**: 定期的なポリシーレビュー、法律顧問相談

### 8. スケジュール

**Day 18**:
- PrivacyService実装
- データ削除API実装
- 自動削除バッチ実装
- テスト実装

**Day 19**:
- プライバシーポリシー作成（ja/en）
- GDPRチェックリスト作成（ja/en）
- 多言語対応確認
- ドキュメント更新

---

## 🔧 実施内容（実績）

### Day 18-19: [日付]
#### 実施作業
- [ ] 作業内容（実装時に記録）

#### 変更ファイル
- ファイル一覧（実装時に記録）

#### 確認・テスト
- [ ] テスト結果（実装時に記録）

#### 課題・気づき
- 課題・気づき（実装時に記録）

---

## 📊 実績

### 達成した成果
- 成果内容（完了時にまとめ）

### プライバシー対応状況
- GDPR準拠状況（完了時にまとめ）

### 学び
- 学んだこと（完了時にまとめ）

---

## ✅ 完了チェックリスト
- [ ] プライバシーポリシー作成完了（ja/en）
- [ ] PII検出・マスキング実装完了
- [ ] データ削除API実装完了
- [ ] 自動削除バッチ実装完了
- [ ] GDPRチェックリスト作成完了（ja/en）
- [ ] 多言語対応確認（ja/en）
- [ ] テスト実装完了
- [ ] ドキュメント更新完了

## 📚 参考資料
- todo.md (1109-1268行目): TODO-8詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/50_data-privacy-in-agentic-ai-gdpr-hipaa-and-developer-best-practices-aaidc-week1-lesson2.md`
- GDPR公式ガイドライン: https://gdpr.eu/

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-18
**担当**: Claude Code
**ステータス**: 計画完了
