from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# PILE번호 버튼 추가: PILE구간 버튼 근처에 배치
if 'CreateButton("PILE번호"' not in text:
    target = '''        CreateButton("PILE구간", 1110, -70, 90, 36, () =>
        {
            ToggleGroupSmart("PILE_SECTION_MARKER");
        });
'''
    insert = target + '''
        CreateButton("PILE번호", 1210, -70, 90, 36, () =>
        {
            if (builder != null)
                builder.TogglePostPileNumberMarkers();
        });
'''
    if target not in text:
        raise SystemExit("PILE구간 버튼 위치를 찾지 못했습니다.")
    text = text.replace(target, insert)

# 기존 바닥구분 버튼이 1210이라 겹치므로 오른쪽으로 이동
text = text.replace(
    'CreateButton("바닥구분", 1210, -70, 90, 36, () =>',
    'CreateButton("바닥구분", 1310, -70, 90, 36, () =>'
)

# allGroups 목록에 추가
if '"POST_PILE_NUMBER_MARKER"' not in text:
    text = text.replace(
'''            "FLOOR_REVIEW_INFO"
        };''',
'''            "FLOOR_REVIEW_INFO",
            "POST_PILE_NUMBER_MARKER"
        };'''
    )

path.write_text(text, encoding="utf-8")
print("UI PILE번호 버튼 추가 완료")
