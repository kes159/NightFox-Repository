import os
import json
import base64
import plistlib
import zipfile
from datetime import datetime
from github import Github  # PyGithub 라이브러리 필요

# --- 1. 설정 및 인증 ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = "kes159/NightFox-Repository"
REPO_URL = f"https://github.com/{REPO_NAME}"
JSON_FILE = "NightFox Repository.json"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- 2. 필수 함수 ---
def extract_ipa_info_only(ipa_path):
    """IPA 파일 내부를 분석하여 정보와 아이콘 데이터를 추출합니다."""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            plist_path = next(f for f in z.namelist() if f.startswith('Payload/') and f.endswith('.app/Info.plist'))
            app_dir = os.path.dirname(plist_path)
            
            with z.open(plist_path) as f:
                plist = plistlib.load(f)
                bundle_id = plist.get('CFBundleIdentifier')
                
                icon_data = None
                try:
                    icon_files = plist.get('CFBundleIcons', {}).get('CFBundlePrimaryIcon', {}).get('CFBundleIconFiles', [])
                    if not icon_files:
                        icon_files = plist.get('CFBundleIconFiles', [])
                    
                    if icon_files:
                        target_icon_name = icon_files[-1]
                        icon_path = next(f for f in z.namelist() if f.startswith(app_dir) and target_icon_name in f and f.endswith('.png'))
                        with z.open(icon_path) as img_f:
                            icon_data = img_f.read()
                except:
                    print(f"⚠️ {ipa_path}에서 아이콘을 찾는 데 실패했습니다.")

                return {
                    'name': plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or ipa_path,
                    'version': plist.get('CFBundleShortVersionString') or "1.0",
                    'bundleID': bundle_id,
                    'size': os.path.getsize(ipa_path),
                    'buildVersion': plist.get('CFBundleVersion'),
                    'icon_data': icon_data
                }
    except Exception as e:
        print(f"⚠️ {ipa_path} 정보 추출 실패: {e}")
        return None

def apply_nightfox_branding(entry):
    """앱 항목에 NightFox 브랜딩을 적용합니다."""
    entry["developerName"] = "NightFox"
    entry["subtitle"] = "NightFox"
    entry["localizedDescription"] = "NightFox"

# --- 3. 기본 데이터 구조 정의 (news 항목 제거) ---
base_data = {
    "name": "NightFox Repository",
    "identifier": "com.nightfox.repo",
    "subtitle": "NightFox's App Repository",
    "description": "Welcome to NightFox's source!",
    "iconURL": "https://i.imgur.com/EVyT7Ji.png",
    "website": REPO_URL,
    "tintColor": "#00b39e",
    "featuredApps": [],
    "apps": [] 
}

# --- 4. 기존 데이터 로드 및 보정 ---
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        try:
            loaded_data = json.load(f)
            base_data['apps'] = loaded_data.get('apps', [])
            
            required_fields = ['name', 'identifier', 'subtitle', 'description', 'iconURL', 'website', 'tintColor']
            for field in required_fields:
                if field in base_data:
                    loaded_data[field] = base_data[field]

            base_data.update(loaded_data)
            base_data['news'] = [] # 기존 news 데이터가 있어도 비움
            
        except Exception as e:
            print(f"기존 JSON 읽기 오류: {e}")
            
# B. 모든 릴리즈에서 실제 IPA 다운로드 주소 수집
all_release_assets = {}
for release in repo.get_releases():
    for asset in release.get_assets():
        if asset.name.lower().endswith('.ipa'):
            if asset.name not in all_release_assets:
                all_release_assets[asset.name] = asset.browser_download_url

# C/D. IPA 파일 처리 및 버전 업데이트
ipa_files = sorted([f for f in os.listdir('.') if f.lower().endswith('.ipa')])

for ipa_file in ipa_files:
    info = extract_ipa_info_only(ipa_file)
    if not info: continue

    current_version = info.get('version', '1.0')
    current_bundle_id = info.get('bundleID')
    download_url = all_release_assets.get(ipa_file) or f"{REPO_URL}/releases/download/latest/{ipa_file.replace(' ', '%20')}"

    app_entry = next((a for a in base_data['apps'] if a.get('bundleIdentifier') == current_bundle_id), None)

    new_v = {
        "version": current_version,
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "localizedDescription": f"NightFox Build - {current_version}",
        "downloadURL": download_url,
        "size": info.get('size', 0),
        "buildVersion": info.get('buildVersion', None)
    }

    if app_entry:
        app_entry["version"] = current_version
        app_entry["downloadURL"] = download_url
        apply_nightfox_branding(app_entry)
        if "versions" not in app_entry: app_entry["versions"] = []
        app_entry["versions"] = [v for v in app_entry["versions"] if v.get('version') != current_version]
        app_entry["versions"].insert(0, new_v)
    else:
        new_app = {
            "name": info.get('name', ipa_file),
            "bundleIdentifier": current_bundle_id,
            "version": current_version,
            "downloadURL": download_url,
            "iconURL": "https://i.imgur.com/nAsnPKq.png",
            "tintColor": "#00b39e",
            "category": "other",
            "versions": [new_v]
        }
        apply_nightfox_branding(new_app)
        base_data['apps'].append(new_app)

# --- 5. 데이터 최종 정제 (news 키 강제 제거) ---
def atomic_clean(obj):
    if isinstance(obj, dict):
        cleaned_dict = {
            k: atomic_clean(v) 
            for k, v in obj.items() 
            if k != "news" and v is not None and v != "" and v != [] and v != {}
        }
        return cleaned_dict
    elif isinstance(obj, list):
        return [atomic_clean(i) for i in obj if i is not None and i != "" and i != [] and i != {}]
    else:
        return obj

base_data = atomic_clean(base_data)

# --- 6. JSON 파일 저장 ---
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(base_data, f, ensure_ascii=False, indent=2)

print(f"🎉 News 항목이 제거된 {JSON_FILE} 생성이 완료되었습니다.")
