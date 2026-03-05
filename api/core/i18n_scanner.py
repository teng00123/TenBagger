#!/usr/bin/env python3
"""
国际化扫描工具
自动扫描Python代码中的翻译文本并填充到PO文件中
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple
import glob


def extract_translation_strings_from_file(file_path: str) -> List[str]:
    """
    从单个Python文件中提取翻译字符串

    Args:
        file_path: Python文件路径

    Returns:
        提取到的翻译字符串列表
    """
    translation_strings = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 方法1: 使用正则表达式匹配 _() 函数调用
        # 匹配 _('text') 或 _("text") 或 _(variable)
        patterns = [
            r"_\(['\"]([^'\"]*)['\"]\)",  # _('text')
            r"_\(['\"]([^'\"]*)['\"],\s*[^)]+\)",  # _('text', locale='xx')
            r"i18n\._\(['\"]([^'\"]*)['\"]\)",  # i18n._('text')
            r"i18n\.t\(['\"]([^'\"]*)['\"]\)",  # i18n.t('text')
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            translation_strings.extend(matches)

        # 方法2: 使用AST解析更精确地提取
        try:
            tree = ast.parse(content)

            class TranslationExtractor(ast.NodeVisitor):
                def __init__(self):
                    self.strings = []

                def visit_Call(self, node):
                    # 检查是否是 _() 函数调用
                    if isinstance(node.func, ast.Name) and node.func.id == '_':
                        if node.args and isinstance(node.args[0], ast.Str):
                            self.strings.append(node.args[0].s)
                    # 检查是否是 i18n._() 或 i18n.t() 调用
                    elif (isinstance(node.func, ast.Attribute) and
                          isinstance(node.func.value, ast.Name) and
                          node.func.value.id == 'i18n' and
                          node.func.attr in ['_', 't']):
                        if node.args and isinstance(node.args[0], ast.Str):
                            self.strings.append(node.args[0].s)

                    self.generic_visit(node)

            extractor = TranslationExtractor()
            extractor.visit(tree)
            translation_strings.extend(extractor.strings)

        except SyntaxError:
            # 如果AST解析失败，只使用正则表达式结果
            pass

    except Exception as e:
        print(f"错误: 无法读取文件 {file_path}: {e}")

    # 去重并返回
    return list(set(translation_strings))


def scan_project_for_translations(project_root: str, patterns: List[str] = None) -> Dict[str, List[str]]:
    """
    扫描整个项目中的翻译字符串

    Args:
        project_root: 项目根目录
        patterns: 要扫描的文件模式，默认为所有.py文件

    Returns:
        字典：文件名 -> 翻译字符串列表
    """
    if patterns is None:
        patterns = ["**/*.py"]

    translation_results = {}

    for pattern in patterns:
        for file_path in glob.glob(os.path.join(project_root, pattern), recursive=True):
            # 跳过venv、__pycache__等目录
            if any(skip in file_path for skip in ['venv', '__pycache__', '.git', '.idea']):
                continue

            strings = extract_translation_strings_from_file(file_path)
            if strings:
                relative_path = os.path.relpath(file_path, project_root)
                translation_results[relative_path] = strings

    return translation_results


def generate_pot_file(translations: Dict[str, List[str]], output_path: str):
    """
    生成POT模板文件

    Args:
        translations: 翻译字符串字典
        output_path: 输出POT文件路径
    """
    pot_content = """# Translations template for TenBagger project.
# Copyright (C) 2026 TenBagger Team
# This file is distributed under the same license as the TenBagger project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2026.
#
msgid ""
msgstr ""
"Project-Id-Version: TenBagger 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2026-03-05 16:52+0800\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: i18n_scanner.py\\n"

"""

    # 收集所有唯一的翻译字符串
    all_strings = set()
    for file_strings in translations.values():
        all_strings.update(file_strings)

    # 按字母顺序排序
    sorted_strings = sorted(all_strings)

    # 添加翻译条目
    for msgid in sorted_strings:
        # 转义特殊字符
        escaped_msgid = msgid.replace('"', '\\"').replace('\n', '\\n')
        pot_content += f'#: {get_file_references(msgid, translations)}\n'
        pot_content += f'msgid "{escaped_msgid}"\n'
        pot_content += 'msgstr ""\n\n'

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pot_content)

    print(f"✅ 已生成POT文件: {output_path}")
    print(f"📊 共找到 {len(sorted_strings)} 个翻译字符串")


def get_file_references(msgid: str, translations: Dict[str, List[str]]) -> str:
    """
    获取字符串在哪些文件中被引用

    Args:
        msgid: 翻译字符串
        translations: 翻译字典

    Returns:
        文件引用字符串
    """
    references = []
    for file_path, strings in translations.items():
        if msgid in strings:
            references.append(file_path)

    return ' '.join(references)


def update_po_file(po_file_path: str, new_translations: Set[str]):
    """
    更新现有的PO文件，添加新的翻译条目

    Args:
        po_file_path: PO文件路径
        new_translations: 新的翻译字符串集合
    """
    if not os.path.exists(po_file_path):
        print(f"❌ PO文件不存在: {po_file_path}")
        return

    # 读取现有PO文件内容
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取现有的msgid
    existing_msgids = set(re.findall(r'msgid "([^"]+)"', content))

    # 找出需要添加的新字符串
    new_msgids = new_translations - existing_msgids

    if not new_msgids:
        print(f"✅ PO文件已是最新，无需更新: {po_file_path}")
        return

    # 在文件末尾添加新条目
    new_content = content.rstrip() + '\n\n'

    for msgid in sorted(new_msgids):
        escaped_msgid = msgid.replace('"', '\\"').replace('\n', '\\n')
        new_content += f'#: i18n_scanner.py (自动添加)\n'
        new_content += f'msgid "{escaped_msgid}"\n'
        new_content += 'msgstr ""\n\n'

    # 写回文件
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ 已更新PO文件: {po_file_path}")
    print(f"📝 新增 {len(new_msgids)} 个翻译条目")


def scan_and_update_translations(project_root: str = None):
    """
    扫描项目并更新所有翻译文件

    Args:
        project_root: 项目根目录，默认为当前目录的上级目录
    """
    if project_root is None:
        # 默认项目根目录为当前文件的上级目录的上级目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    print(f"🔍 开始扫描项目: {project_root}")

    # 扫描项目
    translations = scan_project_for_translations(project_root)

    if not translations:
        print("❌ 未找到任何翻译字符串")
        return

    # 收集所有翻译字符串
    all_strings = set()
    for strings in translations.values():
        all_strings.update(strings)

    print(f"📊 扫描结果:")
    print(f"   文件数量: {len(translations)}")
    print(f"   翻译字符串总数: {len(all_strings)}")

    # 生成POT文件
    locales_dir = os.path.join(project_root, "locales")
    pot_file_path = os.path.join(locales_dir, "messages.pot")

    generate_pot_file(translations, pot_file_path)

    # 更新现有的PO文件
    po_files = glob.glob(os.path.join(locales_dir, "*/LC_MESSAGES/messages.po"))

    for po_file in po_files:
        update_po_file(po_file, all_strings)

    print("\n🎉 翻译文件更新完成！")
    print("\n📋 下一步操作:")
    print("1. 使用 pybabel compile 命令编译翻译文件")
    print("2. 重启应用使翻译生效")
    print("3. 在代码中使用 _('文本') 进行国际化调用")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='国际化扫描工具')
    parser.add_argument('--project-root', help='项目根目录路径')
    parser.add_argument('--scan-only', action='store_true', help='仅扫描，不更新文件')

    args = parser.parse_args()

    if args.scan_only:
        # 仅扫描模式
        project_root = args.project_root or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        translations = scan_project_for_translations(project_root)

        print("📊 扫描结果:")
        for file_path, strings in translations.items():
            print(f"\n📁 {file_path}:")
            for string in sorted(strings):
                print(f"   - {string}")
    else:
        # 完整扫描和更新
        scan_and_update_translations(args.project_root)


if __name__ == "__main__":
    main()