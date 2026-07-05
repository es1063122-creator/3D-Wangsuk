from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 이미 추가되어 있으면 중복 방지
if "ToggleElevationRulerOverlay" not in text:
    method = r'''

    public void ToggleElevationRulerOverlay()
    {
        WangsukFullModelBuilder builder = Object.FindFirstObjectByType<WangsukFullModelBuilder>();
        if (builder == null)
        {
            Debug.LogWarning("[ELEVATION_RULER_UI] WangsukFullModelBuilder를 찾지 못했습니다.");
            return;
        }

        builder.ToggleElevationRuler();
        Debug.Log("[ELEVATION_RULER_UI] 높이자 버튼 클릭");
    }
'''
    idx = text.rfind("}")
    if idx < 0:
        raise SystemExit("WangsukViewerUI.cs 클래스 끝을 찾지 못했습니다.")
    text = text[:idx] + method + "\n" + text[idx:]


# 기존 버튼 생성 라인 근처에 높이자 버튼 추가
# 우선 '바닥구분' 또는 'PILE번호' 버튼 뒤에 붙이는 방식
button_line = None

patterns = [
    r'(.*"바닥구분".*?\n)',
    r'(.*"PILE번호".*?\n)',
    r'(.*"PILE구간".*?\n)',
    r'(.*"도면검토".*?\n)',
]

for p in patterns:
    m = re.search(p, text)
    if m:
        button_line = m.group(1)
        break

if button_line is None:
    raise SystemExit("기존 버튼 생성 라인을 찾지 못했습니다. Select-String 출력이 필요합니다.")

if '"높이자"' not in text:
    stripped = button_line.strip()

    # CreateButton("이름", ... ) 계열이면 그대로 비슷하게 추가
    if "Create" in stripped and "(" in stripped and "=>" in stripped:
        indent = button_line[:len(button_line) - len(button_line.lstrip())]
        new_line = indent + 'CreateButton("높이자", () => ToggleElevationRulerOverlay());\n'
        text = text.replace(button_line, button_line + new_line, 1)

    elif "AddButton" in stripped and "(" in stripped and "=>" in stripped:
        indent = button_line[:len(button_line) - len(button_line.lstrip())]
        new_line = indent + 'AddButton("높이자", () => ToggleElevationRulerOverlay());\n'
        text = text.replace(button_line, button_line + new_line, 1)

    else:
        raise SystemExit("버튼 생성 패턴을 자동 판별하지 못했습니다. Select-String 출력 필요.")

path.write_text(text, encoding="utf-8")
print("높이자 버튼 자동 추가 완료")
