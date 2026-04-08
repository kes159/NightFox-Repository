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
    기존에 사용하시던 로직을 여기에 그대로 붙여넣으세요.
    """
    # [NightFox님의 기존 extract_ipa_info_only 로직을 여기에 복사하세요]
    # 예시 구조: return {'name': ..., 'version': ..., 'bundleID': ..., 'size': ...}
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
            # 파일 이름을 키로 하여 가장 최신 릴리즈의 주소를 저장
            if asset.name not in all_release_assets:
                all_release_assets[asset.name] = asset.browser_download_url
                print(f"찾음: {asset.name} (태그: {release.tag_name})")

# C. 기존 JSON에 적힌 앱들의 링크 업데이트 (재점검 기능)
print("기존 JSON 앱 데이터의 링크를 검증 및 업데이트 중...")
for app in base_data.get("apps", []):
    if "versions" in app:
        for v in app["versions"]:
            # URL에서 파일명을 추출하여 현재 릴리즈 에셋과 매칭
            file_name_in_url = v["downloadURL"].split('/')[-1].replace('%20', ' ')
            actual_url = all_release_assets.get(file_name_in_url)
            
            if actual_url and v["downloadURL"] != actual_url:
                print(f"링크 갱신: {app['name']} ({v['version']})")
                v["downloadURL"] = actual_url
                # 현재 메인 버전 링크도 함께 갱신
                if app["version"] == v["version"]:
                    app["downloadURL"] = actual_url

# D. 로컬 IPA 파일 처리 (새로 추가되거나 업데이트된 파일)
ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]

for ipa_file in ipa_files:
    info = extract_ipa_info_only(ipa_file)
    if not info: continue

    # 릴리즈 에셋에서 실제 주소를 가져오고, 없으면 기본값(1.0) 생성
    download_url = all_release_assets.get(ipa_file)
    if not download_url:
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

    # 앱 목록에서 해당 번들ID 찾기
    app_entry = next((a for a in base_data['apps'] if a['bundleIdentifier'] == info['bundleID']), None)

    if app_entry:
        app_entry["version"] = info['version']
        app_entry["downloadURL"] = download_url
        apply_nightfox_branding(app_entry)
        if "versions" not in app_entry: app_entry["versions"] = []
        # 같은 버전 정보가 있다면 제거 후 최신 데이터 삽입
        app_entry["versions"] = [v for v in app_entry["versions"] if v['version'] != info['version']]
        app_entry["versions"].insert(0, new_v)
    else:
        new_app = {
            "name": info['name'],
            "bundleIdentifier": info['bundleID'],
            "version": info['version'],
            "downloadURL": download_url,
            "iconURL": "https://i.imgur.com/nAsnPKq.png", # 기본 아이콘
            "tintColor": "#00b39e",
            "category": "other",
            "screenshots": [],
            "versions": [new_v]
        }
        apply_nightfox_branding(new_app)
        base_data['apps'].append(new_app)

# --- 5. 최종 결과 저장 ---
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    # 괄호가 깨지지 않도록 깔끔하게 인덴트를 주어 저장
    json.dump(base_data, f, indent=2, ensure_ascii=False)

print(f"🎉 모든 작업이 완료되었습니다! 파일명: {JSON_FILE}")
