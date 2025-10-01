import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

# --- 設定項目 ---
# クロールを開始するウェブサイトのリスト（今回は最初の1つだけ使います）
INPUT_FILE = "domains.txt" 
# 見つかったco.jpドメインを保存するファイル
OUTPUT_FILE = "found_cojp_links.txt"
# --- 設定項目ここまで ---

# 訪問済みのURLを記録するセット（重複アクセスを防ぐため）
visited_urls = set()
# 見つかったco.jpドメインを記録するセット（重複をなくすため）
found_cojp_domains = set()

def crawl(url, base_domain):
    """
    再帰的にページをクロールし、co.jpドメインへのリンクを探す関数
    """
    # 既に訪問済みのURLはスキップ
    if url in visited_urls:
        return
    
    print(f"🔍 クロール中: {url}")
    visited_urls.add(url)

    try:
        # ページを取得
        response = requests.get(url, timeout=10)
        response.raise_for_status() # エラーがあれば例外を発生
        
        # 文字化け対策
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        # ページ内の全ての<a>タグ（リンク）を探す
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # 相対パスを絶対URLに変換 (例: /about.html -> http://example.com/about.html )
            full_url = urljoin(url, href)
            
            # URLの解析
            parsed_url = urlparse(full_url)
            domain = parsed_url.netloc

            # 1. リンク先がco.jpドメインの場合
            if domain.endswith('.co.jp'):
                if domain not in found_cojp_domains:
                    print(f"✨ co.jpドメイン発見: {domain}")
                    found_cojp_domains.add(domain)

            # 2. リンク先が同じウェブサイト内（base_domain）の場合、さらにクロールを続ける
            if domain == base_domain:
                # URLの#以降（ページ内リンク）を無視
                crawl(full_url.split('#')[0], base_domain)

    except requests.RequestException as e:
        print(f"⚠️  アクセス失敗: {url} ({e})")
    except Exception as e:
        print(f"💥 不明なエラー: {url} ({e})")
    
    # サーバー負荷軽減のため少し待つ
    time.sleep(0.5)


def main():
    """
    メイン処理
    """
    try:
        # domains.txtからクロール対象のウェブサイトURLを取得
        with open(INPUT_FILE, "r") as f:
            start_urls = [line.strip() for line in f if line.strip()]
        
        if not start_urls:
            print(f"エラー: {INPUT_FILE} が空です。クロール対象のURLを1つ以上記述してください。")
            return
        
        # 今回は最初の1つのURLのみを対象とする
        start_url = start_urls[0]
        if not start_url.startswith('http' ):
            start_url = 'http://' + start_url
        
        base_domain = urlparse(start_url ).netloc
        print(f"--- クロール開始 ---")
        print(f"対象サイト: {start_url}")
        print(f"ベースドメイン: {base_domain}")
        print(f"--------------------")

        # クロールを開始
        crawl(start_url, base_domain)

        # 結果をファイルに書き出す
        if found_cojp_domains:
            print(f"\n--- 結果 ---")
            print(f"{len(found_cojp_domains)}個のユニークなco.jpドメインが見つかりました。")
            sorted_domains = sorted(list(found_cojp_domains))
            with open(OUTPUT_FILE, "w") as f:
                for domain in sorted_domains:
                    f.write(f"{domain}\n")
            print(f"結果を {OUTPUT_FILE} に保存しました。")
        else:
            print("\nco.jpドメインへのリンクは見つかりませんでした。")

    except FileNotFoundError:
        print(f"エラー: {INPUT_FILE} が見つかりません。")
    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")

if __name__ == "__main__":
    main()

