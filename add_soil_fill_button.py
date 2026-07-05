from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 지층 버튼 근처에 흙채움 버튼 추가
if 'CreateButton("흙채움"' not in text:
    target = '''        CreateButton("지층", 840, -70, 70, 36, () =>
        {
            ToggleGroupSmart("SOIL_ROCK_LAYER");
        });
'''
    insert = target + '''
        CreateButton("흙채움", 1015, -70, 80, 36, () =>
        {
            if (builder != null)
                builder.ToggleSoilFillVolume();
        });
'''
    if target not in text:
        raise SystemExit("지층 버튼 위치를 찾지 못했습니다.")

    text = text.replace(target, insert)

# 기존 지층글씨/구간EL/PILE구간 버튼이 겹치지 않게 오른쪽으로 살짝 이동
text = text.replace(
    'CreateButton("지층글씨", 920, -70, 90, 36, () =>',
    'CreateButton("지층글씨", 1105, -70, 90, 36, () =>'
)

text = text.replace(
    'CreateButton("구간EL", 1020, -70, 80, 36, () =>',
    'CreateButton("구간EL", 1205, -70, 80, 36, () =>'
)

text = text.replace(
    'CreateButton("PILE구간", 1110, -70, 90, 36, () =>',
    'CreateButton("PILE구간", 1295, -70, 90, 36, () =>'
)

text = text.replace(
    'CreateButton("PILE번호", 1210, -70, 90, 36, () =>',
    'CreateButton("PILE번호", 1395, -70, 90, 36, () =>'
)

text = text.replace(
    'CreateButton("바닥구분", 1310, -70, 90, 36, () =>',
    'CreateButton("바닥구분", 1495, -70, 90, 36, () =>'
)

# allGroups 목록에 추가
if '"SOIL_FILL_VOLUME"' not in text:
    text = text.replace(
'''            "POST_PILE_NUMBER_MARKER"
        };''',
'''            "POST_PILE_NUMBER_MARKER",
            "SOIL_FILL_VOLUME"
        };'''
    )

path.write_text(text, encoding="utf-8")
print("UI 흙채움 버튼 추가 완료")
