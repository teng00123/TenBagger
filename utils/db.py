# utils/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 从新的基类文件导入Base
from data.base_model import Base


def get_db_session():
    """获取数据库会话"""
    return SessionLocal()


def init_db():
    """初始化数据库表结构"""
    # 导入 models 模块以注册所有模型

    # 现在 Base 已经包含了 models 中定义的所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功")
    print(f"已创建的表: {Base.metadata.tables.keys()}")
