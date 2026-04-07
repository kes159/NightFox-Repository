import os
import json
import zipfile
import plistlib
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"

def extract_ipa_full_info(ipa_path):
    """IPA에서 AltStudio 필수 정보(ID, 버전, 크기)를 추출합니다."""
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
    except: return None
    return None

def main():
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    if not ipa_files: return

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"name": "NightFox Repository", "apps": []}

    repo_url = os.getenv("REPO_URL", "https://github.com/kes159/NightFox-Repository")
    tag = os.getenv("TAG_NAME", "v1.0")

    for ipa_file in ipa_files:
        info = extract_ipa_full_info(ipa_file)
        if not info: continue

        # 필수 정보 생성
        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        version_date = datetime.now().strftime("%Y-%m-%d")
        
        new_v_info = {
            "version": info['version'],
            "date": version_date,
            "downloadURL": download_url,
            "size": info['size']
        }

        app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)

        if app_entry:
            # 기존 앱 업데이트
            app_entry["version"] = info['version']
            app_entry["versionDate"] = version_date
            app_entry["downloadURL"] = download_url
            app_entry["size"] = info['size']
            
            if "versions" not in app_entry: app_entry["versions"] = []
            app_entry["versions"] = [v for v in app_entry["versions"] if v.get('version') != info['version']]
            app_entry["versions"].insert(0, new_v_info)
            print(f"✅ {info['name']}: 필수 정보 갱신 완료")
        else:
            # 신규 앱 추가 (Short description을 빈칸으로 설정)
            new_app = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "developerName": "NightFox",
                "version": info['version'],
                "versionDate": version_date,
                "downloadURL": download_url,
                "localizedDescription": "", # [수정] 빈칸으로 지정
                "iconURL": "https://i.imgur.com/nAsnPKq.png",
                "tintColor": "#00b39e",
                "size": info['size'],
                "versions": [new_v_info]
            }
            data['apps'].append(new_app)
            print(f"➕ {info['name']}: 새 앱 추가 완료 (설명은 빈칸)")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
