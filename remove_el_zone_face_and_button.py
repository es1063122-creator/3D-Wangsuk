from pathlib import Path
import re

builder = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = builder.read_text(encoding="utf-8")

# BOTTOM_EL_ZONE은 큰 면이 겹쳐서 복잡하므로 생성 호출 주석 처리
text = text.replace(
'''        // C-612~C-619 시공하한선 EL 기준 바닥 구역 색상 표시
        BuildBottomElZones("c605_pf_hpile.json");''',
'''        // BOTTOM_EL_ZONE 큰 면 방식은 모델을 복잡하게 만들어 사용 중지
        // BuildBottomElZones("c605_pf_hpile.json");'''
)

# 혹시 호출만 남아있는 경우도 주석 처리
text = text.replace(
'''        BuildBottomElZones("c605_pf_hpile.json");''',
'''        // BuildBottomElZones("c605_pf_hpile.json");'''
)

builder.write_text(text, encoding="utf-8")
print("Builder: EL구역면 생성 호출 제거 완료")

ui = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
u = ui.read_text(encoding="utf-8")

# EL구역면 버튼 블록 제거
u, n1 = re.subn(
    r'\s*CreateButton\("EL구역면",[\s\S]*?ToggleGroupSmart\("BOTTOM_EL_ZONE"\);[\s\S]*?\}\);',
    '',
    u
)

# 혹시 이름이 EL구역으로 남아있을 때도 제거
u, n2 = re.subn(
    r'\s*CreateButton\("EL구역",[\s\S]*?ToggleGroupSmart\("BOTTOM_EL_ZONE"\);[\s\S]*?\}\);',
    '',
    u
)

ui.write_text(u, encoding="utf-8")
print("UI: EL구역면 버튼 제거 수 =", n1 + n2)
