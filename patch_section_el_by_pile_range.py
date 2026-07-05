from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

old_block_pattern = r'''        // 전개도 확인값 기준 1차 구간 배치\.
        // 정확한 PILE 범위는 다음 단계에서 전개도 PILE NO\. 구간과 더 세분화 가능\.
        CreateSectionElLabelAtPfRange\(group, centers, 1, 97, "EL\(\+30\.44\)", bottomY\);
        CreateSectionElLabelAtPfRange\(group, centers, 98, 190, "EL\(\+31\.00\)", bottomY\);
        CreateSectionElLabelAtPfRange\(group, centers, 191, 280, "EL\(\+31\.00\)", bottomY\);
        CreateSectionElLabelAtPfRange\(group, centers, 281, 365, "EL\(\+29\.54\)", bottomY\);
        CreateSectionElLabelAtPfRange\(group, centers, 366, 405, "기반암층 상단", bottomY\);
        CreateSectionElLabelAtPfRange\(group, centers, 406, 492, "EL\(\+29\.54\)", bottomY\);'''

new_block = '''        // C-612~C-619 굴착계획 전개도 PILE NO. 범위 + 시공하한선 기준
        // C-612 : P001~067        = EL(+30.44)
        // C-613 : P067~131        = EL(+30.44) / EL(+31.00)
        // C-614 : P131~196        = EL(+31.00)
        // C-615 : P196~248        = EL(+31.00)
        // C-616 : P248~306        = EL(+31.00) / EL(+29.54)
        // C-617 : P306~365        = EL(+31.00) / EL(+29.54) / 기반암층 상단
        // C-618 : P365~428        = EL(+31.00) / EL(+29.54)
        // C-619 : P428~492, P001  = EL(+31.00) / EL(+29.54)
        CreateSectionElLabelAtPfRange(group, centers, 1, 67, "P001~067  EL(+30.44)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 67, 131, "P067~131  EL(+30.44/31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 131, 196, "P131~196  EL(+31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 196, 248, "P196~248  EL(+31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 248, 306, "P248~306  EL(+31.00/29.54)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 306, 365, "P306~365  EL(+31.00/29.54/기반암)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 365, 428, "P365~428  EL(+31.00/29.54)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 428, 492, "P428~492  EL(+31.00/29.54)", bottomY);'''

text, n = re.subn(old_block_pattern, new_block, text)

if n == 0:
    print("기존 임시 구간 블록을 찾지 못했습니다. 개별 호출 치환 시도")

    old_calls = [
        '        CreateSectionElLabelAtPfRange(group, centers, 1, 97, "EL(+30.44)", bottomY);',
        '        CreateSectionElLabelAtPfRange(group, centers, 98, 190, "EL(+31.00)", bottomY);',
        '        CreateSectionElLabelAtPfRange(group, centers, 191, 280, "EL(+31.00)", bottomY);',
        '        CreateSectionElLabelAtPfRange(group, centers, 281, 365, "EL(+29.54)", bottomY);',
        '        CreateSectionElLabelAtPfRange(group, centers, 366, 405, "기반암층 상단", bottomY);',
        '        CreateSectionElLabelAtPfRange(group, centers, 406, 492, "EL(+29.54)", bottomY);',
    ]

    for c in old_calls:
        text = text.replace(c, "")

    marker = '        Debug.Log("========== C605 구간별 굴착저면 EL 글씨 생성 ==========");'
    if marker in text and "P001~067  EL(+30.44)" not in text:
        text = text.replace(marker, new_block + "\n\n" + marker)
        print("Debug.Log 앞에 새 PILE 범위 기준 구간EL 블록 삽입 완료")
else:
    print("기존 임시 구간EL 블록을 도면 PILE 범위 기준으로 교체 완료")

# 긴 라벨이 들어가므로 판 크기와 글씨 크기 보정
text = text.replace(
    'CreateSmallFloorTextPlate(group, label, pos, 0.48f, 3.1f, 0.65f);',
    'CreateSmallFloorTextPlate(group, label, pos, 0.38f, 5.2f, 0.72f);'
)

# 위치를 너무 중앙으로 당기지 않고 벽체 안쪽 가까이에 유지
text = text.replace(
    'pos += inward * 2.8f;',
    'pos += inward * 2.2f;'
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
