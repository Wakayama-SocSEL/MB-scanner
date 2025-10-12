"""SQLAlchemyのベースクラスを定義するモジュール

全てのモデルはこのBaseクラスを継承します。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """全てのSQLAlchemyモデルの基底クラス

    このクラスを継承することで、SQLAlchemyのORM機能を使用できます。
    """

    pass
