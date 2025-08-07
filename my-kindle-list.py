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
import msvcrt

is_stop_tool = False
stop_threading_event = threading.Event()

# Windows環境前提(msvcrt)の処理
def check_stop():
    global is_stop_tool
    print("Enterキーを押すとタイトル取得を中断します…")
    while not stop_threading_event.is_set():
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enterキーが押された
                is_stop_tool = True
                print("\n中断中… 処理を停止します。")
                break
        time.sleep(0.1)  # CPU使用率抑えるために小休止

def normalize_title(title):
    title = re.sub(r"\(Japanese Edition\)", "", title, flags=re.IGNORECASE) # (Japanese Edition) を削除
    title = re.sub(r"(vol\.?|第)\d+[巻話章]?", "", title, flags=re.IGNORECASE)  # 巻数「Vol1、vol.2、第3巻、第4話、vol.10章」等の巻数を削除
    title = re.sub(r"\d+[上下]", "", title)  # 6上、13下 等で表現される巻数を削除
    title = re.sub(r"(?<!^)(?<![A-Za-z])\d+(?![A-Za-z])", "", title)  # 英字に隣接せず先頭以外にある数字を削除
    title = re.sub(r"（.*?）", "", title)  # 全角（）とその中身を削除
    title = re.sub(r"【.*?】", "", title)  # 全角【】とその中身を削除
    title = re.sub(r"\(.*?\)", "", title)  # 半角() とその中身を削除
    title = re.sub(r'^([^\x00-\x7F]+).*$', r'\1', title) # 先頭から最初の全角文字列の場合、全角文字列以外がヒットすればそれ以降を全て削除。狼と香辛料XVI ⇒ 狼と香辛料
    return title.strip()

def normalize_title_head(title):
    title = re.split(r"[ 　]", title)[0]
    return title.strip().lower()

def error_exit():
    stop_threading_event.set()
    input("エラーが発生しました。Enterを押してツールを終了してください...")
    exit(1)

windows_user_name = os.getlogin()

# ツール専用のChromeのプロファイルディレクトリを指定、なければ作成する
# 既存プロファイルでブラウザを表示していた場合、それを参照しようとするとエラーとなるため専用のプロファイルを作成している
profile_dir = fr'C:\Users\{windows_user_name}\AppData\Local\Google\Chrome\User Data\MyKindleListProfile'

driver_options = Options()
driver_options.add_argument("--log-level=3")  # エラーログのみ表示
driver_options.add_argument("--disable-logging")
driver_options.add_argument(f'--user-data-dir={profile_dir}')
driver_options.add_argument("--window-size=800,600") 
driver_options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver_service = Service(ChromeDriverManager().install())
driver_service = Service(log_path='NUL')

try: 
    try: 
        web_driver = webdriver.Chrome(service=driver_service, options=driver_options)
        web_driver.get('https://read.amazon.co.jp/kindle-library')
        web_driver.set_script_timeout(60)
        web_driver.maximize_window()
    except Exception as e:
        print(f"Chromeブラウザの起動に失敗しました")
        error_exit()

    # 初回のみ手動でログインが必要（以降は自動ログイン）
    input("ログインが完了したらEnterを押してください...")
    
    start_time = time.time()
    # ここから自動スクロール
    SCROLL_PAUSE_SEC = 0.5
    no_new_elements_scroll_count  = 0
    SCROLL_NO_CHANGE_LIMIT = 120

    print(f"\rタイトル取得中…。取得状況はツール実行時に表示されらブラウザを見てください。")
    print(f"\rツールによって表示されたブラウザは最小化しないでください。")

    # 別スレッドでツール停止の入力待ちをする
    threading.Thread(target=check_stop, daemon=True).start()

    try: 
        scroll_target = web_driver.find_element(By.ID, "library")
    except Exception as e:
        print(f"Kindleライブラリのページが正しく読み込まれていません")
        error_exit()

    # 最初の高さを取得（scroll対象の要素から）
    pos_before_scroll = web_driver.execute_script("return arguments[0].scrollTop", scroll_target)
    # 下へスクロール可能な限りスクロールを行う
    while True:
        if is_stop_tool:
            print(f"処理を中断しました。中断した時点でのタイトルを出力します。")
            break
        # スクロールを最下部まで行う
        try:
            web_driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_target)
        except Exception as e:
            print(f"スクロール処理でエラー発生")
            error_exit()

        # kindleの仕様上最下部にスクロールされて、本の読み込みが行われるため少し待機
        time.sleep(SCROLL_PAUSE_SEC)
        
        # 前回と高さが変わらない場合はスクロールを続ける
        pos_after_scroll = web_driver.execute_script("return arguments[0].scrollTop", scroll_target)   
        if pos_before_scroll == pos_after_scroll:
            no_new_elements_scroll_count  += 1
            if no_new_elements_scroll_count  >= SCROLL_NO_CHANGE_LIMIT:
                # 読み込み完了と見做し終了
                break
        else:
            no_new_elements_scroll_count  = 0
            pos_before_scroll = pos_after_scroll

    stop_threading_event.set()
    print(f"\rタイトル取得完了。テキストファイルに出力開始します。")
    
    # 読み込みが終わったため、書籍タイトルを取得する
    html = web_driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.find_all('div', id=re.compile(r'^title-'))
    book_titles = dict()
    for div in divs:
        p = div.find('p', class_=re.compile(r'^_'))
        if p:
            book_title = p.get_text(strip=True)
            book_title_normalized = normalize_title(book_title)
            book_titles[normalize_title_head(book_title_normalized)] = book_title_normalized

    # ソート（昇順）
    sorted_book_titles = sorted(book_titles.items(), key=lambda x: x[0])

    try:
        with open("kindleの所持書籍タイトル一覧.txt", "w", encoding="utf-8") as f:
            for _, unique_book_title in sorted_book_titles:
                f.write(unique_book_title + "\n")
    except Exception as e:
        print(f"ファイルの書き込みに失敗しました")
        error_exit()

    web_driver.quit()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"出力にかかった時間: {elapsed_time:.2f}秒")

    print(f"\rタイトル一覧出力完了。実行ファイルと同ディレクトリにkindleの所持書籍タイトル一覧.txtが出力されています。")
    input("my-kindle-listを終了するには Enter を押してください...")

except Exception as e:
    print(f"予期しないエラーが発生しました")
finally:
    if 'web_driver' in globals():
        web_driver.quit()