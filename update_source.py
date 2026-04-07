import os
import json
import zipfile
import plistlib
import sys
from datetime import datetime

# --- 설정 (NightFox님 환경 유지) ---
REPO_NAME = "NightFox Repository"
REPO_ID = "com.nightfox.repository"
# 깃허브 주소는 액션에서 동적으로 처리하거나 아래처럼 고정합니다.
RAW_URL = "https://raw.githubusercontent.com/kes159/NightFox-Repository/main/"
JSON_FILE = "NightFox Repository1.json"

def extract_ipa_info(ipa_path):
    """IPA 내부에서 실제 이름, 번들ID, 버전을 추출합니다."""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            # Info.plist 위치 찾기
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
        print(f"Error extracting {ipa_path}: {e}")
        return None

def generate_repo():
    # 액션에서 다운로드받은 파일 이름 (main.yml에서 정한 이름)
    ipa_file = "app.ipa" 
    download_url = os.getenv("DOWNLOAD_URL") # 액션 환경변수에서 가져옴

    if not os.path.exists(ipa_file):
        print("IPA file not found!")
        return

    print(f"🦊 {REPO_NAME} 자동 업데이트 시작 🦊")
    
    info = extract_ipa_info(ipa_file)
    if not info: return

    # 기존 JSON 읽기 (없으면 신규 생성)
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"name": REPO_NAME, "identifier": REPO_ID, "apps": []}

    new_version = {
        "version": info['version'],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "downloadURL": download_url,
        "size": info['size']
    }

    # 앱 리스트 업데이트
    app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)

    if app_entry:
        app_entry["version"] = info['version']
        if "versions" not in app_entry: app_entry["versions"] = []
        # 동일 버전 중복 방지
        app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
        app_entry["versions"].insert(0, new_version)
    else:
        data['apps'].append({
            "name": info['name'],
            "bundleIdentifier": info['bundleID'],
            "developerName": "NightFox",
            "version": info['version'],
            "versionDate": new_version["date"],
            "downloadURL": download_url,
            "localizedDescription": "Verified app by NightFox.",
            "iconURL": f"{RAW_URL}icons/default.png", # 아이콘은 폴더에 미리 넣어둔 파일 사용 권장
            "tintColor": "#00b39e",
            "versions": [new_version]
        })

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✨ 업데이트 완료: {info['name']} ({info['version']})")

if __name__ == "__main__":
    generate_repo()