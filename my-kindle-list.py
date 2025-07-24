from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os
import re
import time
import threading

def check_stop():
    global stop_flag
    input("タイトル取得を中断したい場合は Enter キーを押してください...。\n")
    stop_flag = True
    print(f"中断中...。中断時までのタイトルを出力します。")

def normalize_title(title):
    title = re.sub(r"\(Japanese Edition\)", "", title, flags=re.IGNORECASE) # (Japanese Edition) を削除
    title = re.sub(r"(vol\.?|第)\d+[巻話章]?", "", title, flags=re.IGNORECASE)  # 巻数
    title = re.sub(r"\d+[上下]", "", title)  # 6上、13下
    title = re.sub(r"(?<!^)(?<![A-Za-z])\d+(?![A-Za-z])", "", title)  # 英字に隣接せず先頭以外にある数字を削除
    title = re.sub(r"（.*?）", "", title)  # 全角カッコの残り
    title = re.sub(r"【.*?】", "", title)  # 全角カッコの残り
    title = re.sub(r"\(.*?\)", "", title)  # 半角カッコの残り
    return title.strip()

# 比較用に正規後にスペースも除去
def normalize_title_for_duplicate_check(title):
    title = normalize_title(title)
    # title = re.sub(r"：.*", "", title)  # コロン以降カット（副題消す）
    title = re.split(r"[ 　]", title)[0]
    return title.strip().lower()

profile_name = "Profile 1"
user_name = os.getlogin()
profile_dir = fr'C:\Users\{user_name}\AppData\Local\Google\Chrome\User Data\{profile_name}'

options = Options()
options.add_argument("--log-level=3")  # エラーログのみ表示
options.add_argument("--disable-logging")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument(f'--user-data-dir={profile_dir}')

service = Service(ChromeDriverManager().install())
service = Service(log_path='NUL')

driver = webdriver.Chrome(service=service, options=options)
driver.get('https://read.amazon.co.jp/kindle-library')

# 初回のみ手動でログインが必要（以降は自動ログイン）
input("ログインが完了したらEnterを押してください...")

stop_flag = False

# 別スレッドでユーザー入力待ちをする
threading.Thread(target=check_stop, daemon=True).start()

# ここから自動スクロール
SCROLL_PAUSE_SEC = 1.0
unchanged_count = 0
MAX_UNCHANGED = 20

print(f"\rタイトル出力中…。書籍の数によっては時間がかかります。")
start_time = time.time()

scroll_target = driver.find_element(By.ID, "library")
# 最初の高さを取得（scroll対象の要素から）
pos_before_scroll = driver.execute_script("return arguments[0].scrollTop", scroll_target)
while True:
    if stop_flag:
        print(f"処理を中断しました。中断した時点でのタイトルを出力します。")
        break
    # スクロールを最下部まで行う
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_target)
    time.sleep(SCROLL_PAUSE_SEC)
    pos_after_scroll = driver.execute_script("return arguments[0].scrollTop", scroll_target)
    
    # 高さが変わらない場合はスクロールを続ける
    if pos_before_scroll == pos_after_scroll:
        unchanged_count += 1
        if unchanged_count >= MAX_UNCHANGED:
            # スクロールできないため終了
            break
    else:
        unchanged_count = 0
        pos_before_scroll = pos_after_scroll

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
divs = soup.find_all('div', id=re.compile(r'^title-'))

# スクロール後にタイトルを出力
duplicate_check_set = set()
unique_titles = []
for div in divs:
    p = div.find('p', class_=re.compile(r'^_'))
    if p:
        title = p.get_text(strip=True)
        title_for_check = normalize_title_for_duplicate_check(title)

        if title_for_check not in duplicate_check_set:
            duplicate_check_set.add(title_for_check)
            unique_titles.append(title)

# ここでソート（昇順）
unique_titles.sort()

with open("kindleの所持書籍タイトル一覧.txt", "w", encoding="utf-8") as f:
    for unique_title in unique_titles:
        f.write(normalize_title(unique_title) + "\n")

driver.quit()
end_time = time.time()
elapsed_time = end_time - start_time

print(f"出力にかかった時間: {elapsed_time:.2f}秒")
print(f"\rタイトル一覧出力完了。実行ファイルと同ディレクトリにkindleの所持書籍タイトル一覧.txtが出力されています。")

input("my-kindle-listを終了するには Enter を押してください...")