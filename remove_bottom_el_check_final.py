from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# CreateBlackWorldText 호출문 자체를 주석 처리
patterns = [
    r'\s*CreateBlackWorldText\(textGroup,\s*"BOTTOM EL\|CHECK",\s*new Vector3\(center\.x,\s*bottomY\s*\+\s*0\.35f,\s*center\.z\),\s*1\.45f\);',
    r'\s*CreateBlackWorldText\(textGroup,\s*"BOTTOM EL\\nCHECK",\s*new Vector3\(center\.x,\s*bottomY\s*\+\s*0\.35f,\s*center\.z\),\s*1\.45f\);',
    r'\s*CreateBlackWorldText\(textGroup,\s*"BOTTOM EL\|CHECK",\s*new Vector3\(center\.x,\s*bottomY\s*\+\s*0\.08f,\s*center\.z\),\s*1\.25f\);',
    r'\s*CreateBlackWorldText\(textGroup,\s*"굴착저면\\nEL 검토",\s*new Vector3\(center\.x,\s*bottomY\s*\+\s*0\.08f,\s*center\.z\),\s*1\.25f\);',
]

removed = 0
for p in patterns:
    text, n = re.subn(p, '\n        // BOTTOM EL CHECK 테스트 글씨 제거', text)
    removed += n

path.write_text(text, encoding="utf-8")
print("BOTTOM EL CHECK 제거 처리 수 =", removed)
print("저장 완료")
