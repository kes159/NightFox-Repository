import os
import json
import zipfile
import plistlib

# --- 설정값 ---
JSON_FILE = "NightFox Repository.json"

def extract_bundle_id(ipa_path):
    """IPA에서 매칭을 위한 번들 ID만 최소한으로 추출합니다."""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            plist_candidates = [f for f in z.namelist() if f.count('/') == 2 and f.endswith('Info.plist') and 'Payload/' in f]
            if not plist_candidates:
                plist_candidates = sorted([f for f in z.namelist() if 'Info.plist' in f and 'Payload/' in f], key=len)
            
            for plist_path in plist_candidates:
                with z.open(plist_path) as f:
                    plist = plistlib.load(f)
                    if plist.get('CFBundleExecutable'):
                        return plist.get('CFBundleIdentifier')
        return None
    except:
        return None

def main():
    # 1. IPA 파일 목록 확인
    ipa_files = [f for f in os.listdir('.') if f.lower().endswith('.ipa')]
    if not ipa_files:
        print("ℹ️ 처리할 IPA 파일이 없습니다.")
        return

    # 2. 기존 JSON 로드 (AltStudio에서 작업한 파일)
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print(f"❌ {JSON_FILE} 파일이 없습니다. AltStudio에서 만든 파일을 먼저 올려주세요.")
        return

    repo_url = os.getenv("REPO_URL", "https://github.com/kes159/NightFox-Repository")
    tag = os.getenv("TAG_NAME", "v1.0")

    for ipa_file in ipa_files:
        bundle_id = extract_bundle_id(ipa_file)
        if not bundle_id:
            continue

        # 다운로드 URL 생성
        download_url = f"{repo_url}/releases/download/{tag}/{ipa_file.replace(' ', '%20')}"
        
        # JSON에서 같은 번들 ID를 가진 앱 찾기
        app_found = False
        for app in data.get('apps', []):
            if app.get("bundleIdentifier") == bundle_id:
                # [핵심] 오직 다운로드 링크만 업데이트합니다.
                # 버전, 날짜 등은 AltStudio에서 설정한 값이 유지됩니다.
                app["downloadURL"] = download_url
                
                # 만약 versions 배열이 있다면 첫 번째 항목의 링크만 업데이트 (구조 유지용)
                if "versions" in app and app["versions"]:
                    app["versions"][0]["downloadURL"] = download_url
                
                print(f"✅ {app.get('name', bundle_id)}: 다운로드 링크 삽입 완료")
                app_found = True
                break
        
        if not app_found:
            print(f"⚠️ {ipa_file} (ID: {bundle_id})와 일치하는 앱을 JSON에서 찾지 못했습니다.")

    # 3. 최종 JSON 저장
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"🚀 {JSON_FILE} 업데이트 완료!")

if __name__ == "__main__":
    main()
