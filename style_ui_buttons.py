from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 1) CreateButton 안의 고정 배경색을 버튼별 색상 함수로 교체
text = re.sub(
    r'img\.color\s*=\s*new Color\s*\(\s*0\.08f\s*,\s*0\.08f\s*,\s*0\.08f\s*,\s*0\.92f\s*\)\s*;',
    'img.color = GetButtonColor(text);',
    text
)

# 혹시 값이 조금 다르게 들어간 경우 보정
text = re.sub(
    r'img\.color\s*=\s*new Color\s*\(\s*0\.08f\s*,\s*0\.08f\s*,\s*0\.08f\s*,\s*0\.85f\s*\)\s*;',
    'img.color = GetButtonColor(text);',
    text
)

# 2) 버튼 텍스트 크기 약간 조정
text = text.replace('txt.fontSize = 14;', 'txt.fontSize = 13;')
text = text.replace('txt.fontStyle = FontStyle.Normal;', 'txt.fontStyle = FontStyle.Bold;')

# 3) GetButtonColor 메서드 추가
if "private Color GetButtonColor(string text)" not in text:
    marker = "    private void CreateButton("
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreateButton 메서드 위치를 찾지 못했습니다.")

    color_method = r'''
    private Color GetButtonColor(string text)
    {
        // 1줄: 실행 / 화면
        if (text == "PF+CIP 생성")
            return new Color(0.02f, 0.30f, 0.55f, 0.95f);

        if (text == "3D뷰" || text == "평면뷰")
            return new Color(0.05f, 0.20f, 0.38f, 0.95f);

        // 보기 프리셋
        if (text == "기본보기" || text == "구조물" || text == "굴착지층" || text == "바닥검토" || text == "도면검토")
            return new Color(0.20f, 0.12f, 0.42f, 0.95f);

        if (text == "전체보기")
            return new Color(0.05f, 0.38f, 0.22f, 0.95f);

        if (text == "전체숨김")
            return new Color(0.42f, 0.08f, 0.08f, 0.95f);

        // 구조물
        if (text == "PF" || text == "CIP" || text == "띠장" || text == "버팀" || text == "코너버팀" || text == "앵커" || text == "높이자" || text == "PILE구간" || text == "PILE번호")
            return new Color(0.45f, 0.25f, 0.06f, 0.95f);

        // 토공 / 지층
        if (text == "굴착면" || text == "바닥" || text == "흙채움" || text == "지층" || text == "지층글씨")
            return new Color(0.08f, 0.32f, 0.16f, 0.95f);

        // 검토 보조
        if (text == "EL글씨" || text == "구간EL" || text == "바닥구분" || text == "최종바닥" || text == "동자리")
            return new Color(0.22f, 0.22f, 0.24f, 0.95f);

        return new Color(0.08f, 0.08f, 0.08f, 0.92f);
    }

'''
    text = text[:idx] + color_method + text[idx:]

path.write_text(text, encoding="utf-8")
print("버튼 색상 그룹화 + 글씨 굵게 처리 완료")
