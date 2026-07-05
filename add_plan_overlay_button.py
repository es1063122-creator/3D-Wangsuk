from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

insert = '''        CreateButton("도면", 20, -115, 70, 34, () =>
        {
            if (registry != null) registry.ToggleGroup("PLAN_OVERLAY");
        });'''

if 'ToggleGroup("PLAN_OVERLAY")' in text:
    print("도면 버튼 이미 있음")
else:
    marker = "        CreateSoilLegendUI();"
    if marker in text:
        text = text.replace(marker, marker + "\n\n" + insert)
        print("도면 버튼 추가 완료")
    else:
        print("CreateSoilLegendUI 기준 문구를 찾지 못했습니다.")

path.write_text(text, encoding="utf-8")
print("저장 완료")
