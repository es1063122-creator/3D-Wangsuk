from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 1) 버튼 생성 영역 전체 재작성
start = text.find('        CreateButton("PF+CIP 생성"')
end = text.find('\n    private void CreateButton', start)

if start < 0:
    raise SystemExit('PF+CIP 생성 버튼 시작 위치를 찾지 못했습니다.')

if end < 0:
    raise SystemExit('CreateButton 메서드 시작 위치를 찾지 못했습니다.')

new_buttons = r'''        // =========================
        // WebGL 공개용 UI 정리 버전
        // 1줄: 실행 / 뷰 / 프리셋
        // 2줄: 구조물
        // 3줄: 토공 / 지층 / 검토
        // =========================

        CreateButton("PF+CIP 생성", 20, -20, 130, 38, () =>
        {
            if (builder != null)
            {
                builder.BuildAll();
                if (fitView != null) fitView.Fit3D();
            }
        });

        CreateButton("3D뷰", 160, -20, 75, 38, () =>
        {
            if (fitView != null) fitView.Fit3D();
        });

        CreateButton("평면뷰", 245, -20, 85, 38, () =>
        {
            if (fitView != null) fitView.FitTopView();
        });

        CreateButton("기본보기", 340, -20, 85, 38, () =>
        {
            ApplyViewPreset("basic");
        });

        CreateButton("구조물", 435, -20, 80, 38, () =>
        {
            ApplyViewPreset("structure");
        });

        CreateButton("굴착지층", 525, -20, 90, 38, () =>
        {
            ApplyViewPreset("excavation");
        });

        CreateButton("바닥검토", 625, -20, 90, 38, () =>
        {
            ApplyViewPreset("bottom");
        });

        CreateButton("도면검토", 725, -20, 90, 38, () =>
        {
            ApplyViewPreset("review");
        });

        CreateButton("전체보기", 825, -20, 90, 38, () =>
        {
            ApplyViewPreset("all");
        });

        CreateButton("전체숨김", 925, -20, 90, 38, () =>
        {
            ApplyViewPreset("hide");
        });


        // 2줄: 구조물
        CreateButton("PF", 20, -65, 60, 34, () =>
        {
            ToggleGroupSmart("PF_HPILE");
        });

        CreateButton("CIP", 90, -65, 60, 34, () =>
        {
            ToggleGroupSmart("CIP");
        });

        CreateButton("띠장", 160, -65, 70, 34, () =>
        {
            ToggleGroupSmart("WALE");
            ToggleGroupSmart("WALE_SPEC_REVIEW");
        });

        CreateButton("버팀", 240, -65, 70, 34, () =>
        {
            ToggleGroupSmart("STRUT_L1");
        });

        CreateButton("코너버팀", 320, -65, 90, 34, () =>
        {
            ToggleGroupSmart("CORNER_STRUT_L1");
        });

        CreateButton("앵커", 420, -65, 70, 34, () =>
        {
            ToggleGroupSmart("ANCHOR_L1");
        });

        CreateButton("높이자", 500, -65, 80, 34, () =>
        {
            if (builder != null)
                builder.ToggleElevationRuler();
        });

        CreateButton("PILE구간", 590, -65, 90, 34, () =>
        {
            ToggleGroupSmart("PILE_SECTION_MARKER");
        });

        CreateButton("PILE번호", 690, -65, 90, 34, () =>
        {
            if (builder != null)
                builder.TogglePostPileNumberMarkers();
        });


        // 3줄: 토공 / 지층 / 검토 보조
        CreateButton("굴착면", 20, -110, 80, 34, () =>
        {
            ToggleGroupSmart("EXCAVATION_FACE");
        });

        CreateButton("바닥", 110, -110, 70, 34, () =>
        {
            ToggleGroupSmart("EXCAVATION_BOTTOM");
        });

        CreateButton("흙채움", 190, -110, 80, 34, () =>
        {
            if (builder != null)
                builder.ToggleSoilRockLayerClean();
        });

        CreateButton("지층", 280, -110, 70, 34, () =>
        {
            ToggleGroupSmart("SOIL_ROCK_LAYER");
        });

        CreateButton("지층글씨", 360, -110, 90, 34, () =>
        {
            ToggleGroupSmart("SOIL_ROCK_TEXT");
        });

        CreateButton("EL글씨", 460, -110, 80, 34, () =>
        {
            ToggleGroupSmart("BOTTOM_EL_TEXT");
        });

        CreateButton("구간EL", 550, -110, 80, 34, () =>
        {
            ToggleGroupSmart("SECTION_EL_TEXT");
        });

        CreateButton("바닥구분", 640, -110, 90, 34, () =>
        {
            ToggleGroupSmart("BOTTOM_ZONE_LINE");
        });

        CreateButton("최종바닥", 740, -110, 90, 34, () =>
        {
            ToggleGroupSmart("FINAL_BOTTOM_STEP");
        });

        CreateButton("동자리", 840, -110, 80, 34, () =>
        {
            ToggleGroupSmart("PLAN_VECTOR_OVERLAY");
        });

        CreateSoilLegendUI();
    }
'''

text = text[:start] + new_buttons + text[end:]


# 2) ApplyViewPreset의 allGroups 목록 보강
pattern = r'        string\[\] allGroups = new string\[\]\s*\{[\s\S]*?\n        \};'
new_allgroups = r'''        string[] allGroups = new string[]
        {
            "PF",
            "PF_HPILE",
            "CIP",
            "WALE",
            "WALE_SPEC_REVIEW",
            "STRUT_L1",
            "CORNER_STRUT_L1",
            "ANCHOR_L1",
            "ANCHOR_L1_LEVEL",
            "ANCHOR_L2_LEVEL",
            "ANCHOR_L3_LEVEL",
            "EXCAVATION_FACE",
            "EXCAVATION_BOTTOM",
            "SOIL_ROCK_LAYER",
            "SOIL_ROCK_TEXT",
            "SOIL_FILL_VOLUME",
            "BOTTOM_EL_TEXT",
            "SECTION_EL_TEXT",
            "PILE_SECTION_MARKER",
            "PILE_NUMBER_MARKER",
            "BOTTOM_ZONE_LINE",
            "PLAN_VECTOR_OVERLAY",
            "FINAL_BOTTOM_STEP",
            "PLAN_OVERLAY",
            "BOTTOM_EL_ZONE",
            "FLOOR_REVIEW_INFO",
            "ELEVATION_RULER"
        };'''

text, count = re.subn(pattern, new_allgroups, text, count=1)
if count == 0:
    raise SystemExit('ApplyViewPreset allGroups 목록을 찾지 못했습니다.')


# 3) 전체보기 all 프리셋 추가
hide_block = r'''        if (preset == "hide")
        {
            Debug.Log("보기 프리셋: 전체숨김");
            return;
        }'''

all_block = r'''        if (preset == "hide")
        {
            Debug.Log("보기 프리셋: 전체숨김");
            return;
        }

        if (preset == "all")
        {
            SetManyGroupsActive(true, allGroups);

            if (builder != null)
                builder.SetFloorReviewInfoOverlay(true);

            Debug.Log("보기 프리셋: 전체보기");
            return;
        }'''

if hide_block not in text:
    raise SystemExit('hide 프리셋 블록을 찾지 못했습니다.')

text = text.replace(hide_block, all_block, 1)


# 4) 프리셋에 PF_HPILE / WALE_SPEC_REVIEW 보강
text = text.replace(
'''                "PF",
                "CIP",
                "WALE",''',
'''                "PF",
                "PF_HPILE",
                "CIP",
                "WALE",
                "WALE_SPEC_REVIEW",'''
)

# 중복으로 여러 번 들어간 경우 너무 과하게 중복되지 않도록 단순 정리
text = text.replace('"PF_HPILE",\n                "PF_HPILE",', '"PF_HPILE",')
text = text.replace('"WALE_SPEC_REVIEW",\n                "WALE_SPEC_REVIEW",', '"WALE_SPEC_REVIEW",')

path.write_text(text, encoding="utf-8")
print("WangsukViewerUI.cs UI 버튼 3줄 정리 + 프리셋 보강 완료")
