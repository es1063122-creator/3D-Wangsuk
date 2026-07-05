from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 기존 PLAN_OVERLAY 버튼 블록 제거
pattern = r'\s*CreateButton\("[^"]*도면[^"]*",\s*[^;]+?\{[\s\S]*?ToggleGroup\("PLAN_OVERLAY"\);[\s\S]*?\}\);'
text, n = re.subn(pattern, '', text)

print("기존 도면 버튼 제거 수 =", n)

new_button = '''        CreateButton("도면ON", 340, -30, 80, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("PLAN_OVERLAY");
        });'''

# CreateSoilLegendUI 호출 전에 넣으면 버튼 생성 순서상 안정적
marker = "        CreateSoilLegendUI();"

if marker in text:
    text = text.replace(marker, new_button + "\\n\\n" + marker)
    print("도면ON 버튼을 상단 첫 줄에 추가 완료")
else:
    # fallback: Start 함수 안 마지막 버튼 근처에 강제 삽입
    idx = text.find("    private void CreateSoilLegendUI()")
    if idx > 0:
        text = text[:idx] + new_button + "\\n\\n" + text[idx:]
        print("도면ON 버튼 fallback 삽입 완료")
    else:
        print("삽입 위치를 찾지 못했습니다. UI 파일 확인 필요")

path.write_text(text, encoding="utf-8")
print("저장 완료")
