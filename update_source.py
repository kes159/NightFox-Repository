import os
import json
import zipfile
import plistlib
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"

def extract_basic_info(ipa_path):
    """IPA에서 번들ID와 이름만 최소한으로 추출합니다."""
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
    except: return None

def main():
    # 1. IPA 파일 목록 확인
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    if not ipa_files: return

    # 2. 기존 JSON 로드
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"name": "NightFox Repository", "apps": []}

    repo_url = os.getenv("REPO_URL", "https://github.com/kes159/NightFox-Repository")
    tag = os.getenv("TAG_NAME", "v1.0.0")

    for ipa_file in ipa_files:
        info = extract_basic_info(ipa_file)
        if not info: continue

        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        
        # JSON에서 같은 번들 ID 찾기
        app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)
        
        new_v = {
            "version": info['version'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "downloadURL": download_url,
            "size": info['size']
        }

        if app_entry:
            # 기존 앱: 링크와 버전만 업데이트 (순서 유지)
            app_entry["version"] = info['version']
            app_entry["downloadURL"] = download_url
            app_entry["versionDate"] = new_v["date"]
            if "versions" not in app_entry: app_entry["versions"] = []
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_v)
            print(f"ℹ️ {info['name']}: 기존 앱 링크 업데이트 완료")
        else:
            # 신규 앱: 딕셔너리를 변수에 먼저 담아서 append (문법 에러 방지)
            new_app = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "developerName": "NightFox",
                "version": info['version'],
                "versionDate": new_v["date"],
                "downloadURL": download_url,
                "iconURL": "https://i.imgur.com/nAsnPKq.png", # AltStudio에서 수정 권장
                "tintColor": "#00b39e",
                "versions": [new_v]
            }
            data['apps'].append(new_app) # 리스트 맨 뒤에 추가
            print(f"✅ {info['name']}: 새 앱을 목록 아래에 추가했습니다.")

    # 3. 파일 저장 (이게 실행되어야 JSON이 갱신됨)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
