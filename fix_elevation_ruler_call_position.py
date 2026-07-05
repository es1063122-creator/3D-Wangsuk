from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) 잘못 들어간 ELEVATION_RULER 호출부 전부 제거
text = re.sub(
    r'\s*Debug\.Log\("\[ELEVATION_RULER\] 생성 호출 시작"\);\s*'
    r'BuildElevationRulerFromModelBounds\(\);\s*'
    r'Debug\.Log\("\[ELEVATION_RULER\] 생성 호출 완료"\);\s*',
    '\n',
    text
)

# 2) 기존 주석만 남아있으면 제거
text = text.replace(
    '        // 토공바닥 0m 기준 / 최상단 포스트 캡까지 1m 간격 높이 기준자\n',
    ''
)

# 3) 진짜 전체 3D 생성 흐름 위치에 삽입
target = '''        // 도면 PILE NO 기준 바닥 EL 구간 경계선 표시
        BuildBottomZoneLines("c605_pf_hpile.json");'''

insert = '''        // 도면 PILE NO 기준 바닥 EL 구간 경계선 표시
        BuildBottomZoneLines("c605_pf_hpile.json");

        // 토공바닥 0m 기준 / 최상단 포스트 캡까지 1m 간격 높이 기준자
        Debug.Log("[ELEVATION_RULER] 생성 호출 시작");
        BuildElevationRulerFromModelBounds();
        Debug.Log("[ELEVATION_RULER] 생성 호출 완료");'''

if target not in text:
    raise SystemExit("BuildBottomZoneLines 호출 위치를 찾지 못했습니다.")

text = text.replace(target, insert, 1)

path.write_text(text, encoding="utf-8")
print("ELEVATION_RULER 호출 위치 수정 완료: 전체 3D 생성 흐름에 연결")
