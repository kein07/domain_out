import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

# --- 設定項目 ---
INPUT_FILE = "domains.txt" 
OUTPUT_FILE = "found_cojp_links.txt"
# --- 設定項目ここまで ---

visited_urls = set()
found_cojp_domains = set()

# requestsにリトライ機能を持たせるためのセッションを作成
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3) # 失敗時に3回までリトライ
session.mount('http://', adapter )
session.mount('https://', adapter )


def crawl(url, base_domain):
    if url in visited_urls:
        return
    
    print(f"🔍 クロール中: {url}")
    visited_urls.add(url)

    try:
        # タイムアウトを15秒に延長し、リトライ機能付きのセッションでGET
        response = session.get(url, timeout=15, headers={'User-Agent': 'MyCoJpCrawler/1.0'})
        response.raise_for_status()
        
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            domain = parsed_url.netloc

            if domain.endswith('.co.jp'):
                if domain not in found_cojp_domains:
                    print(f"✨ co.jpドメイン発見: {domain}")
                    found_cojp_domains.add(domain)

            if domain == base_domain:
                crawl(full_url.split('#')[0], base_domain)

    except requests.RequestException as e:
        print(f"⚠️  アクセス失敗: {url} ({e})")
    except Exception as e:
        print(f"💥 不明なエラー: {url} ({e})")
    
    time.sleep(0.5)


def main():
    try:
        with open(INPUT_FILE, "r") as f:
            start_urls = [line.strip() for line in f if line.strip()]
        
        if not start_urls:
            print(f"エラー: {INPUT_FILE} が空です。")
            return
        
        start_url = start_urls[0]
        # httpsを優先的に試すように修正
        if not start_url.startswith('http' ):
            start_url = 'https://' + start_url
        
        base_domain = urlparse(start_url ).netloc
        print(f"--- クロール開始 ---")
        print(f"対象サイト: {start_url}")
        print(f"--------------------")

        crawl(start_url, base_domain)

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
        print(f"致命的なエラー: {e}")

if __name__ == "__main__":
    main()
