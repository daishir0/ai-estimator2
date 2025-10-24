"""入力処理サービス"""
import pandas as pd
from typing import List, Dict
from app.schemas.deliverable import Deliverable
from app.core.i18n import t


class InputService:
    """Excel・CSV入力処理サービス"""

    @staticmethod
    def load_excel_data(excel_path: str) -> List[Dict[str, str]]:
        """Excelファイルから成果物データを読み込む"""
        try:
            df = pd.read_excel(excel_path, engine='openpyxl')

            # A列: 成果物名称, B列: 説明
            if len(df.columns) < 2:
                raise ValueError(t('messages.excel_min_columns'))

            # NaN値を空文字で置換
            df = df.fillna('')

            # 成果物リストを作成
            deliverables = []
            for index, row in df.iterrows():
                if row.iloc[0]:  # 成果物名称が空でない場合のみ追加
                    deliverables.append({
                        'name': str(row.iloc[0]),
                        'description': str(row.iloc[1])
                    })

            return deliverables

        except FileNotFoundError:
            raise FileNotFoundError(f"Excelファイル '{excel_path}' が見つかりません。")
        except Exception as e:
            raise ValueError(t('messages.excel_load_failed').replace('{error}', str(e)))

    @staticmethod
    def load_csv_data(csv_path: str) -> List[Dict[str, str]]:
        """CSVファイルから成果物データを読み込む"""
        try:
            # UTF-8で読み込み、ヘッダー行ありと想定
            df = pd.read_csv(csv_path, encoding='utf-8')

            # 列数チェック
            if len(df.columns) < 2:
                raise ValueError(t('messages.csv_min_columns'))

            # NaN値を空文字で置換
            df = df.fillna('')

            # 成果物リストを作成
            deliverables = []
            for index, row in df.iterrows():
                if row.iloc[0]:  # 成果物名称が空でない場合のみ追加
                    deliverables.append({
                        'name': str(row.iloc[0]),
                        'description': str(row.iloc[1])
                    })

            return deliverables

        except FileNotFoundError:
            raise FileNotFoundError(f"CSVファイル '{csv_path}' が見つかりません。")
        except Exception as e:
            raise ValueError(t('messages.csv_load_failed').replace('{error}', str(e)))

    @staticmethod
    def parse_deliverables_json(deliverables_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Webフォームから送信された成果物JSONを解析"""
        try:
            deliverables = []
            for item in deliverables_data:
                name = item.get('name', '').strip()
                description = item.get('description', '').strip()

                if name:  # 成果物名称が空でない場合のみ追加
                    deliverables.append({
                        'name': name,
                        'description': description
                    })

            if not deliverables:
                raise ValueError("成果物が1件も登録されていません。")

            return deliverables

        except Exception as e:
            raise ValueError(t('messages.deliverable_parse_failed').replace('{error}', str(e)))
