"""pytest 共通設定

テスト実行時にプロジェクトルートを `sys.path` に追加して、
`import src.*` が失敗しないようにする。
"""

import sys
from pathlib import Path

# プロジェクトルート (tests ディレクトリの一つ上の階層)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 既に含まれていなければ sys.path に追加
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
