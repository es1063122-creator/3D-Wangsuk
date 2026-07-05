from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 1) bottom 프리셋 전체 블록을 강제로 교체
pattern = r'''if\s*\(preset\s*==\s*"bottom"\)\s*
\s*\{
.*?Debug\.Log\("보기 프리셋: 바닥검토"\);
\s*return;
\s*\}'''

replacement = '''if (preset == "bottom")
        {
            if (builder != null)
                builder.SetFloorReviewInfoOverlay(true);

            SetManyGroupsActive(true,
                "EXCAVATION_BOTTOM",
                "PLAN_VECTOR_OVERLAY",
                "FINAL_BOTTOM_STEP",
                "SECTION_EL_TEXT",
                "BOTTOM_ZONE_LINE",
                "FLOOR_REVIEW_INFO"
            );

            Debug.Log("보기 프리셋: 바닥검토");
            return;
        }'''

new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)

if count == 0:
    raise SystemExit("bottom 프리셋 블록을 찾지 못했습니다.")

text = new_text

# 2) allGroups 목록에 FLOOR_REVIEW_INFO가 없으면 추가
if '"FLOOR_REVIEW_INFO"' not in text:
    text = text.replace(
'''            "BOTTOM_EL_ZONE"
        };''',
'''            "BOTTOM_EL_ZONE",
            "FLOOR_REVIEW_INFO"
        };'''
    )

path.write_text(text, encoding="utf-8")
print("바닥검토 프리셋 강제 수정 완료")
