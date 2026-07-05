from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

text = text.replace(
'''        // C-605 평면도 STRUT / BEAM-BRACING 레이어 기준
        // 버팀 평면 위치 검토용. 단수/높이는 C-612~C-619 전개도 확인 후 적용.
        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT");''',
'''        // C-605 평면도 STRUT / BEAM-BRACING 레이어 기준
        // C-612~C-619 전개도 분석 결과 STRUT는 WALE 1단 높이군과 일치.
        // 따라서 현재는 STRUT_L1 / CORNER_STRUT_L1 1단만 생성한다.
        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT");'''
)

text = text.replace(
'''        Debug.Log("주의: 현재 버팀은 L1(1단) 평면 검토용만 생성 중. L2/L3는 아직 미적용.");''',
'''        Debug.Log("도면 검토 결과: 현재 STRUT는 WALE 1단 높이군과 일치. L2/L3 STRUT는 전개도에서 확인되지 않아 생성하지 않음.");'''
)

path.write_text(text, encoding="utf-8")
print("STRUT 1단 확정 로그/주석 정리 완료")
