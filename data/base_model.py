# data/base_model.py
"""
模型基类
所有数据模型都应该继承这个基类，以便获得通用功能和配置
"""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# 创建基类
BaseModel = declarative_base()


class ModelMixin:
    """模型混入类，提供通用字段和方法"""

    # 通用字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        """
        将模型实例转换为字典
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            result[column.name] = value
        return result

    def __repr__(self):
        """
        模型的字符串表示
        """
        return f"<{self.__class__.__name__}(id={self.id})>"


# 创建最终的基类，结合 declarative_base 和 ModelMixin
class Base(ModelMixin, BaseModel):
    """
    所有模型的基类
    继承这个类以获得：
    1. 通用字段 (id, created_at, updated_at)
    2. 通用方法 (to_dict, __repr__)
    3. SQLAlchemy 的表定义功能
    """
    __abstract__ = True  # 这是一个抽象基类，不会创建对应的表
