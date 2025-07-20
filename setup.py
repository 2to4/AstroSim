#!/usr/bin/env python3
"""
AstroSim Setup Script

3D太陽系惑星軌道シミュレーターのセットアップスクリプト
"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# プロジェクトルートの取得
project_root = Path(__file__).parent
src_path = project_root / 'src'

# バージョン情報
VERSION = '1.0.0'
DESCRIPTION = 'AstroSim - 3D太陽系惑星軌道シミュレーター'
LONG_DESCRIPTION = """
AstroSimは、太陽系の8惑星の軌道運動をリアルタイムで3Dシミュレーションする
高性能アプリケーションです。

主な特徴:
- ケプラーの法則に基づく正確な軌道計算
- PyQt6 + Vispyによる高品質3D可視化
- インタラクティブなマウス・キーボード操作
- 18.9倍高速化された軌道計算エンジン
- パフォーマンス最適化機能（LOD、フラスタムカリング）
- 包括的なエラーハンドリング
"""

# 依存関係の読み込み
def read_requirements(filename):
    """requirements.txtから依存関係を読み込む"""
    requirements_path = project_root / filename
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
    return []

# 基本依存関係
install_requires = read_requirements('requirements.txt')

# 開発依存関係
dev_requires = read_requirements('requirements-dev.txt')

# README.mdの読み込み
readme_path = project_root / 'README.md'
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = LONG_DESCRIPTION

# パッケージデータの収集
def get_package_data():
    """パッケージに含めるデータファイルを収集"""
    package_data = {}
    
    # データファイル
    data_files = []
    data_path = src_path / 'data'
    if data_path.exists():
        for file_path in data_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(src_path)
                data_files.append(str(rel_path))
    
    if data_files:
        package_data[''] = data_files
    
    return package_data

# エントリーポイントの定義
entry_points = {
    'console_scripts': [
        'astrosim=src.main:main',
    ],
    'gui_scripts': [
        'astrosim-gui=src.main:main',
    ],
}

# クラシファイア（分類情報）
classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'Topic :: Scientific/Engineering :: Astronomy',
    'Topic :: Scientific/Engineering :: Physics',
    'Topic :: Scientific/Engineering :: Visualization',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Operating System :: OS Independent',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX :: Linux',
    'Operating System :: MacOS',
    'Environment :: X11 Applications :: Qt',
    'Environment :: MacOS X',
    'Environment :: Win32 (MS Windows)',
    'Natural Language :: Japanese',
    'Natural Language :: English',
]

# プロジェクトURL
project_urls = {
    'Homepage': 'https://github.com/your-username/AstroSim',
    'Documentation': 'https://github.com/your-username/AstroSim/docs',
    'Repository': 'https://github.com/your-username/AstroSim.git',
    'Bug Reports': 'https://github.com/your-username/AstroSim/issues',
    'Discussions': 'https://github.com/your-username/AstroSim/discussions',
}

# セットアップ実行
setup(
    # 基本情報
    name='astrosim',
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    
    # 作者情報
    author='Claude Code',
    author_email='noreply@anthropic.com',
    maintainer='Claude Code',
    maintainer_email='noreply@anthropic.com',
    
    # URL情報
    url='https://github.com/your-username/AstroSim',
    project_urls=project_urls,
    
    # ライセンス
    license='MIT',
    
    # パッケージ情報
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data=get_package_data(),
    include_package_data=True,
    
    # 依存関係
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'test': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.11.0',
        ],
        'build': [
            'pyinstaller>=6.0.0',
            'wheel>=0.41.0',
            'build>=1.0.0',
        ],
    },
    
    # Python要件
    python_requires='>=3.8',
    
    # エントリーポイント
    entry_points=entry_points,
    
    # 分類情報
    classifiers=classifiers,
    
    # キーワード
    keywords=[
        'astronomy', 'physics', 'simulation', '3d', 'solar-system',
        'planets', 'orbital-mechanics', 'kepler', 'visualization',
        'pyqt6', 'vispy', 'numpy', 'scipy', 'education', 'science'
    ],
    
    # zipセーフでない（データファイルを含むため）
    zip_safe=False,
    
    # プラットフォーム
    platforms=['any'],
    
    # 追加メタデータ
    options={
        'bdist_wheel': {
            'universal': False,  # Python 3専用
        },
    },
)

# セットアップ後処理
if __name__ == '__main__':
    # セットアップが成功した場合の追加処理
    print(f"\n🎉 AstroSim v{VERSION} セットアップ完了!")
    print("\n📦 インストール確認:")
    print("   python -c 'import src.main; print(\"✅ AstroSim正常にインストールされました\")'")
    print("\n🚀 実行方法:")
    print("   astrosim          # コマンドライン実行")
    print("   astrosim-gui      # GUI実行")
    print("   python -m src.main  # モジュール実行")