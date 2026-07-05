from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 도면ON 버튼이 있으면 동자리로 변경
text = text.replace('CreateButton("도면ON"', 'CreateButton("동자리"')
text = text.replace('ToggleGroupSmart("PLAN_OVERLAY");', 'ToggleGroupSmart("PLAN_VECTOR_OVERLAY");')

# 혹시 기존 도면 버튼이 남아 있지 않으면 새로 추가
if 'ToggleGroupSmart("PLAN_VECTOR_OVERLAY")' not in text:
    new_button = '''        CreateButton("동자리", 340, -30, 80, 36, () =>
        {
            ToggleGroupSmart("PLAN_VECTOR_OVERLAY");
        });'''

    marker = "        CreateSoilLegendUI();"
    if marker in text:
        text = text.replace(marker, new_button + "\n\n" + marker)
        print("동자리 버튼 신규 추가 완료")
    else:
        print("동자리 버튼 삽입 기준을 찾지 못했습니다.")
else:
    print("동자리 버튼 연결 완료")

path.write_text(text, encoding="utf-8")
print("저장 완료")
