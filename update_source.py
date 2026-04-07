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
    """IPA 파일에서 메인 앱의 정보를 추출합니다."""
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
                                "size": os.path.getsize(ipa_path),
                                "plist": plist # 권한 정보 수정을 위해 plist 객체 전달
                            }
                except: continue
        return None
    except: return None

# --- 실행 로직 ---
if __name__ == "__main__":
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as f: json.dump({"apps": []}, f)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 현재 폴더의 모든 IPA 파일 처리
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    repo_url = "https://github.com/kes159/NightFox-Repository" # 실제 레포 주소에 맞게 수정 필요
    tag = "1.0" # 실제 릴리즈 태그에 맞게 수정 필요

    for ipa_file in ipa_files:
        info = extract_ipa_info_only(ipa_file)
        if not info: continue

        # 기존 앱 찾기
        app_entry = next((a for a in data['apps'] if a['bundleIdentifier'] == info['bundleID']), None)
        
        # 아이콘 주소 설정 (기존에 있으면 유지, 없으면 기본값)
        current_icon_url = app_entry.get("iconURL", "https://i.imgur.com/nAsnPKq.png") if app_entry else "https://i.imgur.com/nAsnPKq.png"
        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        
        new_v = {
            "version": info['version'], 
            "date": datetime.now().strftime("%Y-%m-%d"), 
            "downloadURL": download_url, 
            "size": info['size'],
            "localizedDescription": "NightFox" # 버전별 설명도 NightFox로 고정
        }

        # 앱 정보 공통 수정 로직 (기존 앱 업데이트든 새 앱 추가든 적용)
        def apply_nightfox_branding(target_dict):
            target_dict["developerName"] = "NightFox"
            target_dict["subtitle"] = "NightFox"
            target_dict["localizedDescription"] = "NightFox"
            
            # infoPlist 내의 권한 설명 자동 수정
            if "appCapabilities" in target_dict and "infoPlist" in target_dict["appCapabilities"]:
                for key in target_dict["appCapabilities"]["infoPlist"]:
                    if key.endswith("UsageDescription"):
                        target_dict["appCapabilities"]["infoPlist"][key] = "NightFox"

        if app_entry:
            # 1. 기존 앱 정보 업데이트
            app_entry["version"] = info['version']
            app_entry["downloadURL"] = download_url
            apply_nightfox_branding(app_entry) # 브랜드 정보 고정
            
            if "versions" not in app_entry: app_entry["versions"] = []
            # 중복 버전 제거 후 최신 버전 삽입
            app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
            app_entry["versions"].insert(0, new_v)
            print(f"ℹ️ {info['name']}: 기존 정보 및 NightFox 브랜딩 업데이트 완료")
        else:
            # 2. 새 앱 추가
            new_app_data = {
                "name": info['name'],
                "bundleIdentifier": info['bundleID'],
                "version": info['version'],
                "versionDate": new_v["date"],
                "downloadURL": download_url,
                "iconURL": current_icon_url,
                "tintColor": "#00b39e",
                "versions": [new_v]
            }
            apply_nightfox_branding(new_app_data) # 브랜드 정보 고정
            data['apps'].append(new_app_data)
            print(f"✅ {info['name']}: 새 앱 추가 및 NightFox 브랜딩 적용 완료")

    # 결과 저장
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
