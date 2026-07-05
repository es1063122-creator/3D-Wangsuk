from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 기존 중복 호출 제거
text = text.replace('        BuildElevationRulerFromModelBounds();\n', '')
text = text.replace('BuildElevationRulerFromModelBounds();\n', '')

# 가장 확실한 위치: BuildSoilRockBandsAndLabels 호출 직후에 삽입
pattern = r'(BuildSoilRockBandsAndLabels\s*\(\s*"c605_pf_hpile\.json"\s*\)\s*;)'

replacement = r'''\1

        Debug.Log("[ELEVATION_RULER] 생성 호출 시작");
        BuildElevationRulerFromModelBounds();
        Debug.Log("[ELEVATION_RULER] 생성 호출 완료");'''

text, count = re.subn(pattern, replacement, text, count=1)

if count == 0:
    raise SystemExit("BuildSoilRockBandsAndLabels 호출부를 찾지 못했습니다. Select-String으로 위치 확인 필요.")

path.write_text(text, encoding="utf-8")
print("ELEVATION_RULER 호출부 강제 연결 완료")
