import os
import json
import zipfile
import plistlib
from datetime import datetime

# --- 사용자 설정 ---
JSON_FILE = "NightFox Repository.json"
IPA_FILE = "app.ipa" # GitHub Action이 내려받을 임시 이름

def extract_ipa_info(ipa_path):
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            plist_path = [f for f in z.namelist() if 'Info.plist' in f and 'Payload/' in f][0]
            with z.open(plist_path) as f:
                plist = plistlib.load(f)
                return {
                    "name": plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or "Unknown App",
                    "bundleID": plist.get('CFBundleIdentifier'),
                    "version": plist.get('CFBundleShortVersionString') or "1.0.0",
                    "size": os.path.getsize(ipa_path)
                }
    except Exception as e:
        print(f"IPA 파싱 에러: {e}")
        return None

def main():
    download_url = os.getenv("DOWNLOAD_URL")
    if not download_url:
        print("다운로드 URL을 찾을 수 없습니다.")
        return

    info = extract_ipa_info(IPA_FILE)
    if not info: return

    # 1. 기존 JSON 읽기
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # 파일이 없으면 기본 구조 생성
        data = {"name": "NightFox Repository", "identifier": "com.nightfox.repository", "apps": []}

    new_version_entry = {
        "version": info['version'],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "downloadURL": download_url,
        "size": info['size']
    }

    # 2. 동일한 앱이 있는지 확인 (Bundle ID 기준)
    app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)

    if app_entry:
        # 기존 앱 업데이트
        app_entry["version"] = info['version']
        app_entry["versionDate"] = new_version_entry["date"]
        app_entry["downloadURL"] = download_url
        if "versions" not in app_entry: app_entry["versions"] = []
        # 중복 버전 제거 후 최상단 추가
        app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
        app_entry["versions"].insert(0, new_version_entry)
    else:
        # 신규 앱 추가
        data['apps'].append({
            "name": info['name'],
            "bundleIdentifier": info['bundleID'],
            "developerName": "NightFox",
            "version": info['version'],
            "versionDate": new_version_entry["date"],
            "downloadURL": download_url,
            "localizedDescription": "Added via NightFox Automation",
            "iconURL": "https://raw.githubusercontent.com/kes159/NightFox-Repository/main/icons/default.png",
            "tintColor": "#00b39e",
            "versions": [new_version_entry]
        })

    # 3. 결과 저장
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 업데이트 완료: {info['name']} ({info['version']})")

if __name__ == "__main__":
    main()