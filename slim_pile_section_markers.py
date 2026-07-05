from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 세로 경계봉 높이 축소
text = text.replace(
'''        float topY = 0.8f;
        float bottomY = -8.0f;''',
'''        float topY = -0.2f;
        float bottomY = -7.6f;'''
)

# 경계봉 두께 축소
text = text.replace(
'''        marker.transform.localScale = new Vector3(0.16f, Mathf.Abs(topY - bottomY), 0.16f);''',
'''        marker.transform.localScale = new Vector3(0.07f, Mathf.Abs(topY - bottomY), 0.07f);'''
)

# 경계봉 색을 반투명 연회색으로
text = text.replace(
'''        mat.color = new Color(1f, 1f, 1f, 0.95f);''',
'''        mat.color = new Color(0.85f, 0.85f, 0.85f, 0.55f);'''
)

# 경계 텍스트를 너무 안쪽으로 보내지 않기
text = text.replace(
'''        Vector3 textPos = p + inward * 2.8f;
        textPos.y = topY + 0.55f;

        CreatePileMarkerText(group, label + "\\n" + sheet, textPos, 0.45f, 3.0f, 0.9f);''',
'''        Vector3 textPos = p + inward * 1.8f;
        textPos.y = 0.45f;

        CreatePileMarkerText(group, label, textPos, 0.24f, 1.4f, 0.42f);'''
)

# 구간 라벨은 일단 제거: 구간EL 라벨과 겹쳐서 복잡함
pattern = r'\s*CreatePileSectionRangeLabel\(group, centers, allCenter, [^;]+?\);\s*'
text, n = re.subn(pattern, '\n        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김\n', text)

# 검정판 크기/투명도 축소
text = text.replace(
'''        plate.transform.localScale = new Vector3(plateWidth, 0.025f, plateDepth);''',
'''        plate.transform.localScale = new Vector3(plateWidth, 0.018f, plateDepth);'''
)

text = text.replace(
'''        plateMat.color = new Color(0f, 0f, 0f, 0.72f);''',
'''        plateMat.color = new Color(0f, 0f, 0f, 0.50f);'''
)

path.write_text(text, encoding="utf-8")
print("PILE구간 마커 축소 완료")
print("숨김 처리한 구간명 라벨 수 =", n)
