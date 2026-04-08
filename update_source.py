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

# --- 2. 필수 함수 (기존 로직 유지 필요) ---
def extract_ipa_info_only(ipa_path):
    """
    IPA 파일에서 이름, 버전, 번들ID, 크기를 추출합니다.
    (NightFox님의 기존 로직이 여기에 들어있어야 합니다.)
    """
    # 실제 구현이 없으면 스크립트가 작동하지 않으므로 주의하세요.
    pass 

def apply_nightfox_branding(entry):
    """앱 항목에 NightFox 브랜딩을 적용합니다."""
    entry["developerName"] = "NightFox"
    entry["subtitle"] = "NightFox"
    entry["localizedDescription"] = "NightFox"

# --- 3. 기본 데이터 구조 정의 ---
base_data = {
    "name": "NightFox Repository",
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

# --- 4. 메인 실행 로직 ---

# A. 기존 JSON 데이터 불러오기
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        try:
            existing_data = json.load(f)
            if "apps" in existing_data:
                base_data["apps"] = existing_data["apps"]
        except: 
            print("기존 JSON을 읽는 중 오류가 발생하여 새로 생성합니다.")

# B. 모든 릴리즈에서 실제 IPA 다운로드 주소 수집
all_release_assets = {}
print("GitHub 모든 릴리즈에서 최신 다운로드 링크를 검색 중...")
for release in repo.get_releases():
    for asset in release.get_assets():
        if asset.name.lower().endswith('.ipa'):
            if asset.name not in all_release_assets:
                all_release_assets[asset.name] = asset.browser_download_url
                print(f"찾음: {asset.name} (태그: {release.tag_name})")

# C. 기존 JSON에 적힌 앱들의 링크 업데이트 (재점검 및 방어 로직 강화)
print("기존 JSON 앱 데이터의 링크를 검증 및 업데이트 중...")
for app in base_data.get("apps", []):
    # [꼼꼼한 수정 1] 필수 키가 없는 앱 항목은 건너뛰기
    if "versions" not in app or "name" not in app:
        print(f"⚠️ 경고: '{app.get('name', '알 수 없는 앱')}' 항목의 구조가 올바르지 않아 건너뜁니다.")
        continue

    for v in app["versions"]:
        # [꼼꼼한 수정 2] 버전 정보가 없는 경우 방어
        if "downloadURL" not in v or "version" not in v:
            continue

        file_name_in_url = v["downloadURL"].split('/')[-1].replace('%20', ' ')
        actual_url = all_release_assets.get(file_name_in_url)
        
        if actual_url and v["downloadURL"] != actual_url:
            print(f"링크 갱신: {app['name']} ({v['version']})")
            v["downloadURL"] = actual_url
            
            # [꼼꼼한 수정 3] KeyError 방지를 위해 .get() 사용
            if app.get("version") == v.get("version"):
                app["downloadURL"] = actual_url

# D. 로컬 IPA 파일 처리
ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]

for ipa_file in ipa_files:
    info = extract_ipa_info_only(ipa_file)
    if not info: 
        print(f"⚠️ {ipa_file}에서 정보를 추출할 수 없어 건너뜁니다.")
        continue

    download_url = all_release_assets.get(ipa_file)
    if not download_url:
        download_url = f"{REPO_URL}/releases/download/1.0/{ipa_file.replace(' ', '%20')}"

    new_v = {
        "version": info.get('version', '1.0'), # 안전하게 get 사용
        "date": datetime.now().strftime("%Y-%m-%d"),
        "localizedDescription": "NightFox", 
        "downloadURL": download_url,
        "size": info.get('size', 0),
        "buildVersion": None,
        "minOSVersion": None
    }

    app_entry = next((a for a in base_data['apps'] if a.get('bundleIdentifier') == info.get('bundleID')), None)

    if app_entry:
        app_entry["version"] = info.get('version', app_entry.get("version"))
        app_entry["downloadURL"] = download_url
        apply_nightfox_branding(app_entry)
        if "versions" not in app_entry: app_entry["versions"] = []
        app_entry["versions"] = [v for v in app_entry["versions"] if v.get('version') != info.get('version')]
        app_entry["versions"].insert(0, new_v)
    else:
        new_app = {
            "name": info.get('name', ipa_file),
            "bundleIdentifier": info.get('bundleID', 'com.unknown'),
            "version": info.get('version', '1.0'),
            "downloadURL": download_url,
            "iconURL": "https://i.imgur.com/nAsnPKq.png",
            "tintColor": "#00b39e",
            "category": "other",
            "screenshots": [],
            "versions": [new_v]
        }
        apply_nightfox_branding(new_app)
        base_data['apps'].append(new_app)

# --- 5. 최종 결과 저장 ---
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(base_data, f, indent=2, ensure_ascii=False)

# [꼼꼼한 수정 4] 변수명을 사용하여 정확한 로그 출력
print(f"🎉 모든 작업이 완료되었습니다! 파일명: {JSON_FILE}")
