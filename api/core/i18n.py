import os
from functools import lru_cache
from babel import Locale
from babel.support import Translations
from fastapi import Request, HTTPException

# 默认语言
DEFAULT_LANGUAGE = "zh_CN"
SUPPORTED_LANGUAGES = ["zh_CN", "en_US"]
DOMAIN = "messages"  # 翻译文件域名

# 获取翻译文件的根目录 (app/locales)
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")


@lru_cache()
def get_translations(locale: str) -> Translations:
    """
    加载并缓存翻译对象
    生产环境中 lru_cache 能有效提高性能，避免重复IO
    """
    return Translations.load(LOCALES_DIR, [locale, DEFAULT_LANGUAGE], DOMAIN)


def get_accept_language(request: Request) -> str:
    """
    从请求头解析语言偏好
    优先级：Query参数 > Header Accept-Language > 默认语言
    """
    # 1. 检查 Query 参数 (例如 ?lang=en_US)
    lang_query = request.query_params.get("lang")
    if lang_query in SUPPORTED_LANGUAGES:
        return lang_query

    # 2. 检查 Header
    accept_language = request.headers.get("Accept-Language")
    if accept_language:
        # 解析 Accept-Language (简单处理，生产可用 babel.Locale.parse)
        # 例如 "en-US,en;q=0.9,zh-CN;q=0.8"
        lang_header = accept_language.split(",")[0].replace("-", "_")
        if lang_header in SUPPORTED_LANGUAGES:
            return lang_header

    return DEFAULT_LANGUAGE


def get_locale(request: Request) -> str:
    """FastAPI 依赖项：获取当前请求的语言代码"""
    return get_accept_language(request)


def translate(key: str, locale: str, **kwargs) -> str:
    """
    翻译函数
    :param key: 原文或标记 (如 "Hello World")
    :param locale: 语言代码
    :param kwargs: 格式化参数 (如 name="User")
    """
    translation = get_translations(locale)
    # gettext 是标准翻译方法
    return translation.gettext(key).format(**kwargs)


class I18n:
    """
    国际化助手类，封装常用方法
    在业务逻辑中使用
    """

    def __init__(self, locale: str):
        self.locale = locale
        self.translation = get_translations(locale)

    def t(self, message: str, **kwargs) -> str:
        """核心翻译方法"""
        return self.translation.gettext(message).format(**kwargs)

    # 常见业务场景快捷方法
    def validation_error(self, field: str):
        # 这里的文本会在 .po 文件中定义
        return self.t("Invalid field: {field}", field=field)


# FastAPI 依赖注入
def get_i18n(request: Request) -> I18n:
    return I18n(get_locale(request))

