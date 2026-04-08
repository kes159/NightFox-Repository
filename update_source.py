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
    """IPA 파일 내부의 Info.plist를 분석하여 실제 정보를 추출합니다."""
    try:
        import zipfile
        import plistlib
        import os

        with zipfile.ZipFile(ipa_path, 'r') as z:
            # Payload/*.app/Info.plist 경로 찾기
            plist_path = next(f for f in z.namelist() if f.startswith('Payload/') and f.endswith('.app/Info.plist'))
            with z.open(plist_path) as f:
                plist = plistlib.load(f)
                return {
                    'name': plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or ipa_path,
                    'version': plist.get('CFBundleShortVersionString') or "1.0",
                    'bundleID': plist.get('CFBundleIdentifier'),
                    'size': os.path.getsize(ipa_path)
                }
    except Exception as e:
        print(f"⚠️ {ipa_path} 정보 추출 실패: {e}")
        return None

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

# C. 기존 JSON 앱 데이터 업데이트 (에러 방지 강화)
print("기존 JSON 앱 데이터의 링크를 검증 및 업데이트 중...")
for app in base_data.get("apps", []):
    # versions 리스트가 없는 항목은 아예 건너뜁니다.
    if "versions" not in app: continue
    
    for v in app["versions"]:
        # v가 딕셔너리가 아니거나 downloadURL이 없으면 패스
        if not isinstance(v, dict) or "downloadURL" not in v: continue
        
        file_name_in_url = v["downloadURL"].split('/')[-1].replace('%20', ' ')
        actual_url = all_release_assets.get(file_name_in_url)
        
        if actual_url and v["downloadURL"] != actual_url:
            print(f"링크 갱신: {app.get('name', '알 수 없는 앱')} ({v.get('version', '?.?')})")
            v["downloadURL"] = actual_url
            
            # 여기서 .get()을 써야 안전합니다.
            if app.get("version") == v.get("version") and app.get("version") is not None:
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
