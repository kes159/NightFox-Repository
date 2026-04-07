import os
import json
import zipfile
import plistlib
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"
REPO_URL = "https://github.com/kes159/NightFox-Repository"
TAG = "1.0"

def extract_ipa_info_only(ipa_path):
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
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
    app_dict["developerName"] = "NightFox"
    app_dict["subtitle"] = "NightFox"
    app_dict["localizedDescription"] = "NightFox"

if __name__ == "__main__":
    # 사이드스토어 필수 헤더를 포함한 기본 구조
    base_data = {
        "name": "NightFox Repository",
        "identifier": "com.nightfox.repo", # 사이드스토어 필수!
        "subtitle": "NightFox's App Repository",
        "description": "Welcome to NightFox's source!",
        "iconURL": "https://i.imgur.com/EVyT7Ji.png",
        "website": REPO_URL,
        "tintColor": "#00b39e",
        "featuredApps": [],
        "news": [ # 일부 사이드스토어 버전에서 필수
            {
                "title": "Source Updated",
                "identifier": "update-" + datetime.now().strftime("%Y%m%d"),
                "caption": "Latest apps added.",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "tintColor": "#00b39e"
            }
        ],
        "apps": []
    }

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
                # 기존 apps 리스트가 있으면 base_data에 합치기
                if "apps" in existing_data:
                    base_data["apps"] = existing_data["apps"]
            except: pass

    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]

    for ipa_file in ipa_files:
        info = extract_ipa_info_only(ipa_file)
        if not info: continue

        download_url = f"{REPO_URL}/releases/download/{TAG}/{ipa_file.replace(' ', '%20')}"
        new_v = {
            "version": info['version'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "localizedDescription": "", 
            "downloadURL": download_url,
            "size": info['size']
        }

        app_entry = next((a for a in base_data['apps'] if a['bundleIdentifier'] == info['bundleID']), None)

        if app_entry:
            app_entry["version"] = info['version']
            app_entry["downloadURL"] = download_url
            apply_nightfox_branding(app_entry)
            if "versions" not in app_entry: app_entry["versions"] = []
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_v)
        else:
            new_app = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "version": info['version'],
                "downloadURL": download_url,
                "iconURL": "https://i.imgur.com/nAsnPKq.png",
                "tintColor": "#00b39e",
                "versions": [new_v]
            }
            apply_nightfox_branding(new_app)
            base_data['apps'].append(new_app)

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(base_data, f, indent=2, ensure_ascii=False)
