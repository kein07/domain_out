import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from collections import deque

# --- 設定項目 ---
INPUT_FILE = "domains.txt" 
OUTPUT_FILE = "found_cojp_links.txt"
MAX_PAGES_TO_CRAWL = 3000 # 上限を少し増やし、時間内に終わるかテスト
# 優先的にクロールしたいページのURLに含まれるキーワード
PRIORITY_KEYWORDS = ['news', 'release', 'partner', 'policy', 'sitemap', 'company', 'about']
# --- 設定項目ここまで ---

visited_urls = set()
found_cojp_domains = set()

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount('http://', adapter )
session.mount('https://', adapter )

def crawl_page(url, base_domain, normal_queue, priority_queue):
    if url in visited_urls:
        return
    
    print(f"[{len(visited_urls) + 1}/{MAX_PAGES_TO_CRAWL}] 🔍 クロール中: {url}")
    visited_urls.add(url)

    try:
        response = session.get(url, timeout=15, headers={'User-Agent': 'MyCoJpCrawler/1.0'})
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href).split('#')[0] # URLの#以降は無視
            
            if not full_url.startswith('http' ):
                continue

            parsed_url = urlparse(full_url)
            domain = parsed_url.netloc

            # co.jpドメインを発見
            if domain.endswith('.co.jp'):
                if domain not in found_cojp_domains:
                    print(f"✨ co.jpドメイン発見: {domain}")
                    found_cojp_domains.add(domain)

            # 同じサイト内の未訪問ページをキューに追加
            if domain == base_domain and full_url not in visited_urls:
                # 優先キーワードが含まれていれば、優先キューに追加
                if any(keyword in full_url for keyword in PRIORITY_KEYWORDS):
                    priority_queue.append(full_url)
                else:
                    normal_queue.append(full_url)
    except Exception as e:
        print(f"⚠️  アクセス失敗 or パースエラー: {url} ({e})")

def main():
    print("--- 賢いクローラーを開始します ---")
    start_time = time.time()
    
    try:
        with open(INPUT_FILE, "r") as f:
            start_url = f.readline().strip()
        if not start_url:
            print("エラー: domains.txtが空です。")
            return

        if not start_url.startswith('http' ):
            start_url = 'https://' + start_url
        
        base_domain = urlparse(start_url ).netloc
        
        # 優先キューと通常キューを用意
        priority_queue = deque()
        normal_queue = deque([start_url])

        print(f"対象サイト: {start_url}")
        print(f"クロール上限: {MAX_PAGES_TO_CRAWL} ページ")
        print("--------------------")

        # クロール実行ループ
        while (priority_queue or normal_queue) and len(visited_urls) < MAX_PAGES_TO_CRAWL:
            # 優先キューを先に処理
            if priority_queue:
                current_url = priority_queue.popleft()
            else:
                current_url = normal_queue.popleft()
            
            crawl_page(current_url, base_domain, normal_queue, priority_queue)
            time.sleep(0.2) # 待機時間を少し短縮

        # 結果の書き出し
        if found_cojp_domains:
            print(f"\n--- 結果 ---")
            print(f"{len(found_cojp_domains)}個のユニークなco.jpドメインが見つかりました。")
            with open(OUTPUT_FILE, "w") as f:
                f.write("\n".join(sorted(list(found_cojp_domains))))
            print(f"結果を {OUTPUT_FILE} に保存しました。")
        else:
            print("\nco.jpドメインへのリンクは見つかりませんでした。")

    except Exception as e:
        print(f"致命的なエラー: {e}")
    finally:
        end_time = time.time()
        print(f"\n--- プログラム終了 ---")
        print(f"総実行時間: {end_time - start_time:.2f} 秒")
        print(f"訪問済みページ数: {len(visited_urls)}")

if __name__ == "__main__":
    main()
