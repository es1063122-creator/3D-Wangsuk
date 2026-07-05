from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 기존 C605 앙카 호출을 PF번호 구간 기준 앙카 호출로 확실히 교체
text = re.sub(
    r'BuildAnchorL1FromDxf\s*\(\s*"c605_anchor_l1\.json"\s*,\s*"ANCHOR_L1"\s*\)\s*;',
    'BuildAnchorSpecReviewFromPfCenters("c605_pf_hpile.json", "ANCHOR_L1");',
    text,
    count=1
)

# 혹시 줄바꿈 때문에 세미콜론이 분리된 경우까지 처리
text = re.sub(
    r'BuildAnchorL1FromDxf\s*\(\s*"c605_anchor_l1\.json"\s*,\s*"ANCHOR_L1"\s*\)\s*\n\s*;',
    'BuildAnchorSpecReviewFromPfCenters("c605_pf_hpile.json", "ANCHOR_L1");',
    text,
    count=1
)

# 앙카 투명도 더 높임
text = text.replace(
    'CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.18f))',
    'CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.10f))'
)

text = text.replace(
    'CreateAnchorSpecMaterial(new Color(1.0f, 0.18f, 0.02f, 0.38f))',
    'CreateAnchorSpecMaterial(new Color(1.0f, 0.18f, 0.02f, 0.22f))'
)

# 앙카 본체 더 얇게
text = text.replace(
    'anchor.transform.localScale = new Vector3(0.11f, 0.11f, displayLen);',
    'anchor.transform.localScale = new Vector3(0.055f, 0.055f, displayLen);'
)

text = text.replace(
    'anchor.transform.localScale = new Vector3(0.12f, 0.12f, displayLen);',
    'anchor.transform.localScale = new Vector3(0.055f, 0.055f, displayLen);'
)

text = text.replace(
    'anchor.transform.localScale = new Vector3(0.18f, 0.18f, displayLen);',
    'anchor.transform.localScale = new Vector3(0.055f, 0.055f, displayLen);'
)

# 머리점도 작게
text = text.replace(
    'headSphere.transform.localScale = Vector3.one * 0.34f;',
    'headSphere.transform.localScale = Vector3.one * 0.20f;'
)

text = text.replace(
    'headSphere.transform.localScale = Vector3.one * 0.42f;',
    'headSphere.transform.localScale = Vector3.one * 0.20f;'
)

text = text.replace(
    'headSphere.transform.localScale = Vector3.one * 0.55f;',
    'headSphere.transform.localScale = Vector3.one * 0.20f;'
)

path.write_text(text, encoding="utf-8")
print("앙카 호출부 교체 + 굵기/투명도 낮춤 완료")
