from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# PILE_NO_TEXT 위치/크기 강화
text = text.replace(
    'txtObj.transform.localPosition = new Vector3(0f, 0.16f, 0f);',
    'txtObj.transform.localPosition = new Vector3(0f, 0.42f, 0f);'
)

text = text.replace(
    'tm.fontSize = 130;',
    'tm.fontSize = 220;'
)

text = text.replace(
    'tm.characterSize = 0.062f;',
    'tm.characterSize = 0.078f;'
)

# PILE_NO_TEXT TextMesh 뒤에 WebGL용 재질 강제 적용 블록 삽입
old = '''        tm.color = Color.black;
        tm.richText = false;'''

new = '''        tm.color = Color.black;
        tm.richText = false;
        tm.fontStyle = FontStyle.Bold;

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = txtObj.GetComponent<MeshRenderer>();
            if (mr != null && font.material != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.black;
                textMat.renderQueue = 6000;
                mr.sharedMaterial = textMat;
            }
        }'''

# 첫 번째 파일번호 TextMesh 블록만 확실히 교체
idx = text.find('GameObject txtObj = new GameObject("PILE_NO_TEXT_"')
if idx >= 0:
    next_idx = text.find(old, idx)
    if next_idx >= 0:
        text = text[:next_idx] + new + text[next_idx + len(old):]
        print("PILE_NO_TEXT WebGL 강제 표시 패치 완료")
    else:
        print("주의: PILE_NO_TEXT tm.color/tm.richText 블록을 찾지 못했습니다.")
else:
    print("주의: PILE_NO_TEXT 생성 블록을 찾지 못했습니다.")

path.write_text(text, encoding="utf-8")
