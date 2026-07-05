from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

insert = '''        CreateButton("PILE구간", 1110, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("PILE_SECTION_MARKER");
        });'''

if 'ToggleGroup("PILE_SECTION_MARKER")' in text:
    print("PILE구간 버튼 이미 있음")
else:
    old = '''        CreateButton("구간EL", 1020, -70, 80, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("SECTION_EL_TEXT");
        });'''

    if old in text:
        text = text.replace(old, old + "\n\n" + insert)
        print("구간EL 버튼 뒤에 PILE구간 버튼 추가 완료")
    else:
        print("구간EL 버튼 기준 문구를 찾지 못했습니다. UI 파일 확인 필요")

path.write_text(text, encoding="utf-8")
print("저장 완료")
