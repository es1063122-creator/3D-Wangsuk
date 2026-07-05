from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

insert = '''        CreateButton("굴착면", 580, -70, 80, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("EXCAVATION_FACE");
        });

        CreateButton("바닥", 670, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("EXCAVATION_BOTTOM");
        });

        CreateButton("EL글씨", 750, -70, 80, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("BOTTOM_EL_TEXT");
        });'''

if 'ToggleGroup("EXCAVATION_FACE")' in text:
    print("굴착면/바닥/EL글씨 버튼 이미 있음")
else:
    # 앵커 버튼 뒤에 추가 시도
    old_anchor = '''        CreateButton("앵커", 420, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("ANCHOR_L1");
        });'''

    old_excav = '''        CreateButton("굴착", 500, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("EXCAVATION_FLOOR");
        });'''

    if old_excav in text:
        text = text.replace(old_excav, old_excav + "\n\n" + insert)
        print("기존 굴착 버튼 뒤에 굴착면/바닥/EL글씨 버튼 추가 완료")
    elif old_anchor in text:
        text = text.replace(old_anchor, old_anchor + "\n\n" + insert)
        print("앵커 버튼 뒤에 굴착면/바닥/EL글씨 버튼 추가 완료")
    else:
        print("삽입 기준 버튼을 찾지 못했습니다. UI 파일 확인 필요")

path.write_text(text, encoding="utf-8")
print("저장 완료")
