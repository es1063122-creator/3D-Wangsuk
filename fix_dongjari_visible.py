from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 동자리 라인 높이: 바닥보다 위로 올림
text = text.replace(
    'float y = -6.58f;',
    'float y = -6.18f;'
)

# 검정선은 검은 바닥에 묻히므로 밝은 선으로 변경
text = text.replace(
    'mat.color = new Color(0.02f, 0.02f, 0.02f, 0.92f);',
    'mat.color = new Color(1f, 1f, 1f, 0.88f);'
)

# 선 두께 확대
text = text.replace(
    'lr.startWidth = 0.028f;',
    'lr.startWidth = 0.055f;'
)
text = text.replace(
    'lr.endWidth = 0.028f;',
    'lr.endWidth = 0.055f;'
)

path.write_text(text, encoding="utf-8")
print("동자리 선 높이/색상/두께 수정 완료")
