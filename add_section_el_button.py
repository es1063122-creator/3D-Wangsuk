from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

insert = '''        CreateButton("구간EL", 1020, -70, 80, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("SECTION_EL_TEXT");
        });'''

if 'ToggleGroup("SECTION_EL_TEXT")' in text:
    print("구간EL 버튼 이미 있음")
else:
    old = '''        CreateButton("지층글씨", 920, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("SOIL_ROCK_TEXT");
        });'''

    if old in text:
        text = text.replace(old, old + "\n\n" + insert)
        print("지층글씨 버튼 뒤에 구간EL 버튼 추가 완료")
    else:
        print("지층글씨 버튼 기준 문구를 찾지 못했습니다. UI 파일 확인 필요")

path.write_text(text, encoding="utf-8")
print("저장 완료")
