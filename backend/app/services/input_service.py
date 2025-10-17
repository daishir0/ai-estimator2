"""入力処理サービス"""
import pandas as pd
from typing import List, Dict
from app.schemas.deliverable import Deliverable


class InputService:
    """Excel入力処理サービス"""

    @staticmethod
    def load_excel_data(excel_path: str) -> List[Dict[str, str]]:
        """Excelファイルから成果物データを読み込む"""
        try:
            df = pd.read_excel(excel_path, engine='openpyxl')

            # A列: 成果物名称, B列: 説明
            if len(df.columns) < 2:
                raise ValueError("Excelファイルには少なくとも2列（成果物名称、説明）が必要です。")

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
            raise ValueError(f"Excelファイルの読み込みに失敗しました: {e}")
