import os
import json
import zipfile
import plistlib
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"
REPO_URL = "https://github.com/kes159/NightFox-Repository" # NightFox님의 레포 주소
TAG = "1.0" # 현재 릴리즈 태그

def extract_ipa_info_only(ipa_path):
    """IPA 파일에서 정보를 추출합니다."""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            # Info.plist 찾기
            plist_candidates = [f for f in z.namelist() if f.count('/') == 2 and f.endswith('Info.plist') and 'Payload/' in f]
            if not plist_candidates:
                plist_candidates = sorted([f for f in z.namelist() if 'Info.plist' in f and 'Payload/' in f], key=len)

            for plist_path in plist_candidates:
                try:
                    with z.open(plist_path) as f:
                        plist = plistlib.load(f)
                        if plist.get('CFBundleExecutable'):
                            return {
                                "name": plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or "Unknown App",
                                "bundleID": plist.get('CFBundleIdentifier'),
                                "version": plist.get('CFBundleShortVersionString') or "1.0.0",
                                "size": os.path.getsize(ipa_path)
                            }
                except: continue
        return None
    except: return None

def apply_nightfox_branding(app_dict):
    """지정한 3곳에만 NightFox 브랜딩을 적용합니다."""
    # 요청하신 대로 딱 이 3개만 수정합니다.
    app_dict["developerName"] = "NightFox"
    app_dict["subtitle"] = "NightFox"
    app_dict["localizedDescription"] = "NightFox"
    
    # Privacy(권한 설명) 부분은 삭제하거나 수정하지 않고 
    # IPA에서 추출된 원본 데이터를 그대로 유지하도록 이 함수에서는 건드리지 않습니다.

if __name__ == "__main__":
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump({"apps": []}, f)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]

    for ipa_file in ipa_files:
        info = extract_ipa_info_only(ipa_file)
        if not info: continue

        download_url = f"{REPO_URL}/releases/download/{TAG}/{ipa_file.replace(' ', '%20')}"
        
        new_version_entry = {
            "version": info['version'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "localizedDescription": ""Release!",
            "downloadURL": download_url,
            "size": info['size']
        }

        app_entry = next((a for a in data['apps'] if a['bundleIdentifier'] == info['bundleID']), None)

        if app_entry:
            # 1. 기존 앱 업데이트
            app_entry["version"] = info['version']
            app_entry["versionDate"] = new_version_entry["date"]
            app_entry["downloadURL"] = download_url
            
            # 브랜딩 적용 (Privacy는 건드리지 않음)
            apply_nightfox_branding(app_entry)
            
            if "versions" not in app_entry: app_entry["versions"] = []
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_version_entry)
            print(f"ℹ️ {info['name']}: 업데이트 완료 (Privacy 유지)")
        else:
            # 2. 새 앱 추가
            new_app = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "version": info['version'],
                "versionDate": new_version_entry["date"],
                "downloadURL": download_url,
                "iconURL": "https://i.imgur.com/nAsnPKq.png", 
                "tintColor": "#00b39e",
                "category": "other",
                "versions": [new_version_entry]
            }
            apply_nightfox_branding(new_app)
            data['apps'].append(new_app)
            print(f"✅ {info['name']}: 새 앱 추가 완료 (Privacy 유지)")

    # 결과 저장
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
