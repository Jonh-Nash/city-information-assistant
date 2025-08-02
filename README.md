# City Information Assistant

本リポジトリは都市情報を対話形式で提供する Web API のリファレンス実装です。テストはすべてメモリ上のリポジトリを用いており、外部データベースを必要としません。

---

## ローカル環境でのテスト実行手順

以下では **Python 標準の仮想環境 (`venv`)** を例に説明します。`pyenv` や `conda` などを利用している場合も基本的な流れは同じです。

### 1. 前提条件

- Python 3.11 以上がインストールされていること
- Git がインストールされていること

### 2. リポジトリのクローン

```bash
git clone <YOUR_FORK_URL> city-information-assistant
cd city-information-assistant
```

### 3. 仮想環境の作成と有効化

```bash
# 仮想環境を作成 (.venv ディレクトリに作成します)
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

仮想環境が有効になると、プロンプトの前に `(.venv)` が表示されます。

### 4. 依存関係のインストール

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` にはテスト実行に必要な `pytest` / `pytest-asyncio` も含まれています。

### 5. テストの実行

```bash
pytest -q
```

`-q` オプションは簡潔な出力 (quiet mode) にするためのものです。詳細ログが必要な場合は省略してください。

### 6. 仮想環境の終了

作業が終わったら以下で仮想環境を解除できます。

```bash
deactivate
```
