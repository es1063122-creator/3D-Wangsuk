from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

text = text.replace(
    '        BuildCornerStrutPlanFromDxf("c605_beam_bracing.json", "CORNER_STRUT");',
    '        // BuildCornerStrutPlanFromDxf("c605_beam_bracing.json", "CORNER_STRUT"); // 가시설 도면 전체 검토 전까지 비활성화'
)

text = text.replace(
    '        BuildCornerStrutsFromPfCenters("c605_pf_hpile.json", "CORNER_STRUT");',
    '        // BuildCornerStrutsFromPfCenters("c605_pf_hpile.json", "CORNER_STRUT"); // 가시설 도면 전체 검토 전까지 비활성화'
)

path.write_text(text, encoding="utf-8")
print("임의/부분 코너스트러트 생성 호출 비활성화 완료")
