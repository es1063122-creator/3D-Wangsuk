from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 경계봉을 더 낮고 얇게
text = text.replace(
'''        float topY = -0.2f;
        float bottomY = -7.6f;''',
'''        float topY = -1.0f;
        float bottomY = -7.2f;'''
)

text = text.replace(
'''        marker.transform.localScale = new Vector3(0.07f, Mathf.Abs(topY - bottomY), 0.07f);''',
'''        marker.transform.localScale = new Vector3(0.035f, Mathf.Abs(topY - bottomY), 0.035f);'''
)

# 경계봉 색을 더 흐리게
text = text.replace(
'''        mat.color = new Color(0.85f, 0.85f, 0.85f, 0.55f);''',
'''        mat.color = new Color(0.85f, 0.85f, 0.85f, 0.28f);'''
)

# PILE 경계 텍스트를 더 작게, 벽체 가까이
text = text.replace(
'''        Vector3 textPos = p + inward * 1.8f;
        textPos.y = 0.45f;

        CreatePileMarkerText(group, label, textPos, 0.24f, 1.4f, 0.42f);''',
'''        Vector3 textPos = p + inward * 1.15f;
        textPos.y = -0.55f;

        CreatePileMarkerText(group, label, textPos, 0.18f, 0.9f, 0.32f);'''
)

# PILE 라벨판 검정 배경을 더 투명하게
text = text.replace(
'''        plateMat.color = new Color(0f, 0f, 0f, 0.50f);''',
'''        plateMat.color = new Color(0f, 0f, 0f, 0.32f);'''
)

# 혹시 남아 있는 구간명 라벨 호출은 계속 숨김
text = re.sub(
    r'\s*CreatePileSectionRangeLabel\(group, centers, allCenter, [^;]+?\);\s*',
    '\n        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김\n',
    text
)

path.write_text(text, encoding="utf-8")
print("PILE구간 마커 초소형 정리 완료")
