from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 기존 버팀 버튼이 STRUT를 보고 있으면 STRUT_L1로 변경
text = text.replace(
'''registry.ToggleGroup("STRUT");''',
'''registry.ToggleGroup("STRUT_L1");'''
)

# 코너버팀 버튼 추가
if 'ToggleGroup("CORNER_STRUT_L1")' in text:
    print("코너버팀 버튼 이미 있음")
else:
    old = '''        CreateButton("버팀", 240, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("STRUT_L1");
        });'''

    new = '''        CreateButton("버팀", 240, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("STRUT_L1");
        });

        CreateButton("코너버팀", 320, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("CORNER_STRUT_L1");
        });'''

    if old in text:
        text = text.replace(old, new)
        print("코너버팀 버튼 추가 완료")
    else:
        print("버팀 버튼 기준 문구를 찾지 못했습니다. UI 파일을 확인해야 합니다.")

path.write_text(text, encoding="utf-8")
print("저장 완료")
