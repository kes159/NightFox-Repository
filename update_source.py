import os
import json
import zipfile
import plistlib
from datetime import datetime

JSON_FILE = "NightFox Repository.json"

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
        print(f"Error parsing {ipa_path}: {e}")
        return None

def main():
    # 현재 폴더에 있는 모든 .ipa 파일 목록 가져오기
    ipa_files = [f for f in os.listdir('.') if f.endswith('.ipa')]
    if not ipa_files:
        print("처리할 IPA 파일이 없습니다.")
        return

    # 기존 JSON 읽기
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"name": "NightFox Repository", "identifier": "com.nightfox.repository", "apps": []}

    for ipa_file in ipa_files:
        info = extract_ipa_info(ipa_file)
        if not info: continue

        # 릴리스 자산 이름을 기반으로 다운로드 URL 추측 (GitHub 규칙 반영)
        # 실제 URL은 main.yml에서 환경변수로 넘겨주는 것이 정확하지만, 
        # 여러 파일 처리 시에는 파일명을 활용합니다.
        repo_url = os.getenv("REPO_URL") # https://github.com/사용자/저장소
        tag = os.getenv("TAG_NAME")
        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file}"

        new_version = {
            "version": info['version'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "downloadURL": download_url,
            "size": info['size']
        }

        app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)

        if app_entry:
            app_entry["version"] = info['version']
            if "versions" not in app_entry: app_entry["versions"] = []
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_version)
            app_entry["downloadURL"] = download_url
        else:
            data['apps'].append({
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "developerName": "NightFox",
                "version": info['version'],
                "versionDate": new_version["date"],
                "downloadURL": download_url,
                "localizedDescription": "Added via NightFox Automation",
                "iconURL": "https://raw.githubusercontent.com/kes159/NightFox-Repository/main/icons/default.png",
                "tintColor": "#00b39e",
                "versions": [new_version]
            })
        print(f"처리 완료: {info['name']}")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
