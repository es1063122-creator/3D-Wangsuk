from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) 깊이감 보정 함수 덩어리 제거
markers = [
    "// WebGL/공개용 시각 보정:",
    "private void ApplyInsideBottomOutsideCapHeight",
    "public void ReapplyBottomReviewDepthEffect"
]

# GetWebSafeShader 앞에 실험 함수들이 들어간 경우가 많으므로 그 앞까지만 정리
shader_idx = text.find("private Shader GetWebSafeShader")
if shader_idx < 0:
    shader_idx = text.find("private string LoadReviewJsonText")
if shader_idx < 0:
    shader_idx = len(text)

cut_start = -1
for m in markers:
    idx = text.rfind(m, 0, shader_idx)
    if idx >= 0:
        if cut_start < 0 or idx < cut_start:
            cut_start = idx

if cut_start >= 0 and shader_idx > cut_start:
    text = text[:cut_start] + "\n\n    " + text[shader_idx:]
    print("깨진 깊이감 보정 함수 블록 제거 완료")
else:
    print("큰 함수 블록 위치를 찾지 못함. 개별 제거 진행")

# 2) 남아 있는 깊이감 보정 호출 라인 제거
text = re.sub(r'^\s*ApplyInsideBottomOutsideCapHeight\(".*?"\);\s*\n', '', text, flags=re.MULTILINE)
text = re.sub(r'^\s*if\s*\(GameObject\.Find\(".*?"\)\s*!=\s*null\)\s*\n\s*ApplyInsideBottomOutsideCapHeight\(".*?"\);\s*\n', '', text, flags=re.MULTILINE)
text = re.sub(r'^\s*if\s*\(builder\s*!=\s*null\)\s*builder\.ReapplyBottomReviewDepthEffect\(\);\s*\n', '', text, flags=re.MULTILINE)

# 3) 혹시 함수 선언만 남아 있으면 제거
text = re.sub(r'\n\s*public void ReapplyBottomReviewDepthEffect\s*\(\)\s*\{\s*\}', '\n', text)
text = re.sub(r'\n\s*private void ApplyInsideBottomOutsideCapHeight\s*\(string groupName\)\s*\{\s*\}', '\n', text)

path.write_text(text, encoding="utf-8")
