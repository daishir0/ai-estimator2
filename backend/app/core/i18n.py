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
