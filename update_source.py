import os
import json
import zipfile
import plistlib
import shutil
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"
ICON_DIR = "icons"

def extract_ipa_info(ipa_path):
    """IPA 파일에서 필요한 정보를 추출합니다."""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            plist_candidates = [f for f in z.namelist() if f.count('/') == 2 and f.endswith('Info.plist') and 'Payload/' in f]
            if not plist_candidates:
                plist_candidates = sorted([f for f in z.namelist() if 'Info.plist' in f and 'Payload/' in f], key=len)

            for plist_path in plist_candidates:
                with z.open(plist_path) as f:
                    plist = plistlib.load(f)
                    if plist.get('CFBundleExecutable'):
                        return {
                            "name": plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or "Unknown App",
                            "bundleID": plist.get('CFBundleIdentifier'),
                            "version": plist.get('CFBundleShortVersionString') or "1.0.0",
                            "size": os.path.getsize(ipa_path)
                        }
        return None
    except:
        return None

def main():
    # 1. IPA 파일 목록 확인
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    if not ipa_files:
        print("ℹ️ 처리할 IPA 파일이 없습니다.")
        return

    # 2. 기존 JSON 로드
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"name": "NightFox Repository", "apps": []}

    repo_url = os.getenv("REPO_URL", "https://github.com/kes159/NightFox-Repository")
    tag = os.getenv("TAG_NAME", "v1.0")

    for ipa_file in ipa_files:
        info = extract_ipa_info(ipa_file)
        if not info:
            continue

        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        version_date = datetime.now().strftime("%Y-%m-%d")
        
        new_version_info = {
            "version": info['version'],
            "date": version_date,
            "downloadURL": download_url,
            "size": info['size']
        }

        # JSON 내에서 같은 앱 찾기
        app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)

        if app_entry:
            # [기존 앱] 업데이트: 순서는 유지하고 정보만 갱신
            app_entry["version"] = info['version']
            app_entry["versionDate"] = version_date
            app_entry["downloadURL"] = download_url
            if "versions" not in app_entry:
                app_entry["versions"] = []
            # 중복 버전 제거 후 최상단에 추가
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_version_info)
            print(f"ℹ️ {info['name']}: 기존 앱 정보 업데이트 완료")
        else:
            # [새 앱] 추가: 데이터를 변수에 담은 후 리스트 맨 뒤(append)에 추가
            new_app = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "developerName": "NightFox",
                "version": info['version'],
                "versionDate": version_date,
                "downloadURL": download_url,
                "iconURL": "https://i.imgur.com/nAsnPKq.png", # 나중에 AltStudio에서 수정 가능
                "tintColor": "#00b39e",
                "versions": [new_version_info]
            }
            data['apps'].append(new_app)
            print(f"✅ {info['name']}: 새 앱을 목록 맨 아래에 추가했습니다.")

    # 3. 결과 저장
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"🚀 {JSON_FILE} 파일 갱신 완료!")

if __name__ == "__main__":
    main()