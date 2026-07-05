from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

insert = '''        CreateButton("EL구역", 1310, -70, 80, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("BOTTOM_EL_ZONE");
        });'''

if 'ToggleGroup("BOTTOM_EL_ZONE")' in text:
    print("EL구역 버튼 이미 있음")
else:
    old = '''        CreateButton("바닥구분", 1210, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("BOTTOM_ZONE_LINE");
        });'''

    if old in text:
        text = text.replace(old, old + "\n\n" + insert)
        print("바닥구분 버튼 뒤에 EL구역 버튼 추가 완료")
    else:
        print("바닥구분 버튼 기준 문구를 찾지 못했습니다. UI 파일 확인 필요")

path.write_text(text, encoding="utf-8")
print("저장 완료")
