def extract_ipa_info_and_icon(ipa_path):
    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            # 1. Info.plist 정보 추출 (동일)
            plist_path = [f for f in z.namelist() if 'Info.plist' in f and 'Payload/' in f][0]
            with z.open(plist_path) as f:
                plist = plistlib.load(f)
                info = {
                    "name": plist.get('CFBundleDisplayName') or plist.get('CFBundleName') or "Unknown App",
                    "bundleID": plist.get('CFBundleIdentifier'),
                    "version": plist.get('CFBundleShortVersionString') or "1.0.0",
                    "size": os.path.getsize(ipa_path)
                }

            # 2. 아이콘 추출 (차선책 알고리즘)
            if not os.path.exists(ICON_DIR):
                os.makedirs(ICON_DIR)
            
            all_pngs = [f for f in z.namelist() if f.lower().endswith('.png') and 'payload' in f.lower()]
            
            target_icon = None
            
            # [차선책 1] 표준 이름 패턴 찾기
            standards = [f for f in all_pngs if any(x in f.lower() for x in ['appicon60', 'appicon120', 'icon-60', 'icon-76'])]
            if standards:
                target_icon = max(standards, key=lambda x: z.getinfo(x).file_size)
            
            # [차선책 2] 표준이 없으면 'icon' 단어가 들어간 파일 중 최대 용량
            if not target_icon:
                icons = [f for f in all_pngs if 'icon' in f.lower()]
                if icons:
                    target_icon = max(icons, key=lambda x: z.getinfo(x).file_size)
            
            # [차선책 3] 그것도 없으면 Payload 내 모든 PNG 중 최대 용량 (고화질 이미지)
            if not target_icon and all_pngs:
                target_icon = max(all_pngs, key=lambda x: z.getinfo(x).file_size)

            # 파일 저장
            if target_icon:
                dest_path = os.path.join(ICON_DIR, f"{info['bundleID']}.png")
                with z.open(target_icon) as source, open(dest_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                info["icon_path"] = f"icons/{info['bundleID']}.png"
            else:
                info["icon_path"] = None

            return info
    except Exception as e:
        print(f"아이콘 추출 중 오류 발생: {e}")
        return None
