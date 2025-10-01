import requests
import time

try:
    with open("domains.txt", "r") as f:
        domains = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("domains.txtが見つかりません。")
    exit()

unused_domains = []
for domain in domains:
    try:
        requests.get(f"http://{domain}", timeout=5 )
        print(f"✅ 使用中: {domain}")
    except requests.exceptions.ConnectionError:
        print(f"❌ 未使用の可能性: {domain}")
        unused_domains.append(domain)
    except Exception as e:
        print(f"❓ 不明なエラー: {domain} ({e})")
    time.sleep(1)

if unused_domains:
    with open("unused_domains.txt", "w") as f:
        f.write("\n".join(unused_domains))
    print("\n結果を unused_domains.txt に保存しました。")
else:
    print("\n未使用のドメインは見つかりませんでした。")
