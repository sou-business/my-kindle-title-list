# 📚 My Kindle Title List

kindleライブラリから購入した書籍の「シリーズを含むタイトル」を抽出し整理するために作成しました。  
Amazon Kindle の所持書籍タイトル一覧をウェブページのDOM（Document Object Model）から自動取得し、重複を除去してテキストファイルに出力するツールです。  
Amazonに手動ログイン後、自動でページを遷移しすべての書籍タイトルを収集します。

作成経緯とか課題：https://qiita.com/soujiro/items/7e81845dbc5dc1cfb864

## ✨ 機能概要

- Kindleライブラリにある **所持書籍タイトルを一覧取得**
- **重複・不要な番号などを自動削除して整形**
- 結果を `kindleの所持書籍タイトル一覧.txt` に出力
- 書籍が多い場合でも **Enterキーで中断可**（途中まで出力）

## ※注意点
- kindleライブラリ (https://read.amazon.co.jp/kindle-library) のウェブページDOMからタイトルテキストを抽出し、  
正規表現で重複を除去しているため、完全な重複排除は難しいです。  
そのため、kindleライブラリ内のシリーズ作品や所持書籍の整理・把握の補助ツールとしてご利用ください。

- 初回の手動ログイン以降、実行毎のログイン不要とするため専用のchromeプロファイルが作成されます。不要であれば削除してください。
   `C:\Users\%USERNAME%\AppData\Local\Google\Chrome\`MyKindleListProfile

## 📦 使用技術

- Python 3.11+
- [Selenium](https://www.selenium.dev/)
- Google Chrome + ChromeDriver

## 🖥️ 動作環境

- OS: Windows 11
- ブラウザ: Google Chrome（最新版）
- Python仮想環境を推奨（`venv`）

## 🔧 セットアップ手順

1. このリポジトリをクローン  
1. 仮想環境の作成 py -m venv .venv
   ```
   py -m venv .venv
   ```
1. 仮想環境を生成したディレクトリで、仮想環境をアクティブ化（Windowsの場合）  
   ```powershell
   .\venv\Scripts\activate
1. 仮想環境で以下を実行して、ビルド＆依存関係にあるモジュールをインストール
   ```powershell
   pip install build
   pip install -e .
1. my-kindle-list.pyを実行してください
   ```powershell
   python my-kindle-list.py

## exeを作成したい場合
   ```powershell
   pip install pyinstaller
   pyinstaller my-kindle-list.py
   ```
以下ディレクトリにexeファイルが生成される   
- my-kindle-title-list\dist\my-kindle-list
