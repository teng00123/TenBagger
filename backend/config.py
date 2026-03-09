import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置"""
    
    # API 配置
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # 交易配置
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 100000))
    COMMISSION_RATE = float(os.getenv("COMMISSION_RATE", 0.0003))  # 万分之三
    
    # 数据源配置
    DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")  # mock 或 real
    YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com"
    
    # 策略配置
    DEFAULT_SYMBOLS = ["600519.SS", "000001.SZ", "BTC-USD"]
    
    @classmethod
    def get_config(cls):
        return {
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "debug": cls.DEBUG,
            "initial_capital": cls.INITIAL_CAPITAL,
            "commission_rate": cls.COMMISSION_RATE,
            "data_source": cls.DATA_SOURCE,
            "default_symbols": cls.DEFAULT_SYMBOLS
        }
