import os
import json
import base64
import plistlib
import zipfile
from datetime import datetime
from github import Github  # PyGithub 필요

# --- 1. 설정 및 인증 (기존 정보 유지) ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = "kes159/NightFox-Repository"
REPO_URL = f"https://github.com/{REPO_NAME}"
JSON_FILE = "NightFox_Repository.json"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- 2. 기존 함수들 (이게 꼭 있어야 함) ---
def extract_ipa_info_only(ipa_path):
    # (NightFox님이 사용하시던 IPA 정보 추출 함수 코드를 여기에 그대로 두세요)
    # 기존 코드에서 extract_ipa_info_only 함수 부분을 복사해서 여기 넣으시면 됩니다.
    pass 

def apply_nightfox_branding(entry):
    # (NightFox님이 사용하시던 브랜딩 함수 코드를 여기에 그대로 두세요)
    entry["developerName"] = "NightFox"
    entry["subtitle"] = "NightFox"
    entry["localizedDescription"] = "NightFox"

# --- 3. 실행 로직 (여기서부터 제가 새로 드린 코드입니다) ---
base_data = {
    "name": "NightFox_Repository",
    "identifier": "com.nightfox.repo",
    "subtitle": "NightFox's App Repository",
    "description": "Welcome to NightFox's source!",
    "iconURL": "https://i.imgur.com/EVyT7Ji.png",
    "website": REPO_URL,
    "tintColor": "#00b39e",
    "featuredApps": [],
    "news": [
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

# 기존 JSON 데이터 불러오기
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        try:
            existing_data = json.load(f)
            if "apps" in existing_data:
                base_data["apps"] = existing_data["apps"]
        except: pass

all_release_assets = {}
print("모든 릴리즈에서 IPA 파일을 검색 중...")

# 모든 릴리즈를 뒤져서 실제 다운로드 주소 확보
for release in repo.get_releases():
    for asset in release.get_assets():
        if asset.name.lower().endswith('.ipa'):
            if asset.name not in all_release_assets:
                all_release_assets[asset.name] = asset.browser_download_url
                print(f"찾음: {asset.name} (릴리즈: {release.tag_name})")

# 로컬 파일과 매칭
ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]

for ipa_file in ipa_files:
    info = extract_ipa_info_only(ipa_file)
    if not info: continue

    download_url = all_release_assets.get(ipa_file)
    if not download_url:
        # 릴리즈에 없을 경우의 대비책 (현재는 1.0을 기본으로 하거나 에러 표시)
        download_url = f"{REPO_URL}/releases/download/1.0/{ipa_file.replace(' ', '%20')}"

    new_v = {
        "version": info['version'],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "localizedDescription": "NightFox", 
        "downloadURL": download_url,
        "size": info['size'],
        "buildVersion": None,
        "minOSVersion": None
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
            "category": "other",
            "screenshots": [],
            "versions": [new_v]
        }
        apply_nightfox_branding(new_app)
        base_data['apps'].append(new_app)

# 4. 파일 저장 및 괄호 닫기 보장
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(base_data, f, indent=2, ensure_ascii=False)

print(f"업데이트 완료: {JSON_FILE}")
