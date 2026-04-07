import os
import json
import zipfile
import plistlib
import shutil
from datetime import datetime

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"
ICON_DIR = "icons"

def extract_ipa_info_only(ipa_path):
    """부속 파일이 아닌 진짜 앱 정보만 추출하도록 필터링을 강화합니다."""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            plist_candidates = [f for f in z.namelist() if f.count('/') == 2 and f.endswith('Info.plist') and 'Payload/' in f]
            if not plist_candidates:
                plist_candidates = sorted([f for f in z.namelist() if 'Info.plist' in f and 'Payload/' in f], key=len)

            for plist_path in plist_candidates:
                with z.open(plist_path) as f:
                    plist = plistlib.load(f)
                    if plist.get('CFBundleExecutable') and plist.get('LSRequiresIPhoneOS') is not None:
                        return {
                            "name": plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or "Unknown App",
                            "bundleID": plist.get('CFBundleIdentifier'),
                            "version": plist.get('CFBundleShortVersionString') or "1.0.0",
                            "size": os.path.getsize(ipa_path)
                        }
        return None
    except: return None

def extract_icon_logic(ipa_path, bundle_id):
    """IPA에서 최선의 아이콘을 추출하여 저장합니다."""
    try:
        if not os.path.exists(ICON_DIR): os.makedirs(ICON_DIR)
        with zipfile.ZipFile(ipa_path, 'r') as z:
            all_pngs = [f for f in z.namelist() if f.lower().endswith('.png') and 'payload' in f.lower()]
            target_icon = None
            standards = [f for f in all_pngs if any(x in f.lower() for x in ['appicon60', 'appicon120', 'icon-60', 'icon-76'])]
            if standards: target_icon = max(standards, key=lambda x: z.getinfo(x).file_size)
            if not target_icon:
                icons = [f for f in all_pngs if 'icon' in f.lower()]
                if icons: target_icon = max(icons, key=lambda x: z.getinfo(x).file_size)
            if not target_icon and all_pngs: target_icon = max(all_pngs, key=lambda x: z.getinfo(x).file_size)

            if target_icon:
                dest_path = os.path.join(ICON_DIR, f"{bundle_id}.png")
                with z.open(target_icon) as source, open(dest_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                return f"icons/{bundle_id}.png"
        return None
    except: return None

def main():
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    if not ipa_files: return

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # 기본 JSON 구조 유지
        data = {
            "name": "NightFox Repository", 
            "subtitle": "NightFox's App Repository",
            "description": "Welcome to my source!",
            "apps": []
        }

    repo_url = os.getenv("REPO_URL", "https://github.com/kes159/NightFox-Repository")
    raw_url = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/"
    tag = os.getenv("TAG_NAME", "v1.0.0")

    for ipa_file in ipa_files:
        info = extract_ipa_info_only(ipa_file)
        if not info: continue

        app_entry = next((item for item in data['apps'] if item["bundleIdentifier"] == info['bundleID']), None)
        
        current_icon_url = None
        if app_entry and app_entry.get("iconURL"):
            current_icon_url = app_entry["iconURL"]
        else:
            icon_path = extract_icon_logic(ipa_file, info['bundleID'])
            current_icon_url = f"{raw_url}{icon_path}" if icon_path else "https://i.imgur.com/nAsnPKq.png"

        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        new_version_info = {
            "version": info['version'], 
            "date": datetime.now().strftime("%Y-%m-%d"), 
            "downloadURL": download_url, 
            "size": info['size']
        }

        if app_entry:
            # 기존 앱 업데이트
            app_entry["version"] = info['version']
            app_entry["iconURL"] = current_icon_url
            app_entry["downloadURL"] = download_url
            if "versions" not in app_entry: app_entry["versions"] = []
            # 중복 버전 제거 후 최신 버전 추가
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_version_info)
            print(f"ℹ️ {info['name']}: 정보를 업데이트했습니다.")
        else:
            # [수정된 핵심 로직] 신규 앱 데이터를 딕셔너리로 생성 후 append
            new_app_data = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "developerName": "NightFox",
                "version": info['version'],
                "versionDate": new_version_info["date"],
                "downloadURL": download_url,
                "iconURL": current_icon_url,
                "tintColor": "#00b39e",
                "versions": [new_version_info]
            }
            data['apps'].append(new_app_data) # 리스트 맨 마지막에 추가
            print(f"✅ {info['name']}: 목록 맨 아래에 새로 추가되었습니다.")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
