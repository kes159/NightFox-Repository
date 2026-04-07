import os
import json
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"

def main():
    # 1. 릴리스에 올라온 IPA 파일들 확인
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    if not ipa_files:
        print("❌ 처리할 IPA 파일이 없습니다.")
        return

    # 2. 기존 JSON 로드
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print("❌ JSON 파일을 찾을 수 없습니다. AltStudio에서 만든 파일을 먼저 올려주세요.")
        return

    repo_url = os.getenv("REPO_URL", "https://github.com/kes159/NightFox-Repository")
    tag = os.getenv("TAG_NAME", "")

    # 3. IPA 파일명을 순회하며 JSON 정보 업데이트
    for ipa_file in ipa_files:
        # 파일명에서 앱 이름을 대략적으로 유추 (매칭용)
        # 예: "Delta_1.6.ipa" -> "Delta"
        clean_name = ipa_file.replace(".ipa", "").split("_")[0].split(".")[0].lower()
        
        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        
        # JSON에서 이름이 비슷한 앱 찾기
        for app in data.get('apps', []):
            if clean_name in app['name'].lower() or clean_name in app['bundleIdentifier'].lower():
                # 다운로드 링크와 날짜만 업데이트
                app['downloadURL'] = download_url
                app['versionDate'] = datetime.now().strftime("%Y-%m-%d")
                if "versions" in app and app['versions']:
                    app['versions'][0]['downloadURL'] = download_url
                    app['versions'][0]['date'] = app['versionDate']
                
                print(f"✅ {app['name']}의 다운로드 링크를 업데이트했습니다.")

    # 4. 저장
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
