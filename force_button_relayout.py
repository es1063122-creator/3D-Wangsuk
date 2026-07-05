from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

start = text.find('        CreateButton("PF+CIP 생성"')
end = text.find('\n    private void CreateButton', start)

if start < 0:
    raise SystemExit('CreateButton("PF+CIP 생성" 시작 위치를 찾지 못했습니다.')

if end < 0:
    raise SystemExit('private void CreateButton 메서드 시작 위치를 찾지 못했습니다.')

new_block = r'''        // ================================
        // 공개용 WebGL UI 버튼 정리
        // 1줄: 실행/뷰
        // 2줄: 보기 프리셋
        // 3줄: 구조물
        // 4줄: 토공/검토
        // ================================

        CreateButton("PF+CIP 생성", 20, -20, 130, 34, () =>
        {
            if (builder != null)
            {
                builder.BuildAll();
                if (fitView != null) fitView.Fit3D();
            }
        });

        CreateButton("3D뷰", 160, -20, 75, 34, () =>
        {
            if (fitView != null) fitView.Fit3D();
        });

        CreateButton("평면뷰", 245, -20, 85, 34, () =>
        {
            if (fitView != null) fitView.FitTopView();
        });

        CreateButton("전체보기", 340, -20, 90, 34, () =>
        {
            ApplyViewPreset("all");
        });

        CreateButton("전체숨김", 440, -20, 90, 34, () =>
        {
            ApplyViewPreset("hide");
        });


        // 2줄: 보기 프리셋
        CreateButton("기본보기", 20, -60, 90, 34, () =>
        {
            ApplyViewPreset("basic");
        });

        CreateButton("구조물", 120, -60, 80, 34, () =>
        {
            ApplyViewPreset("structure");
        });

        CreateButton("굴착지층", 210, -60, 90, 34, () =>
        {
            ApplyViewPreset("excavation");
        });

        CreateButton("바닥검토", 310, -60, 90, 34, () =>
        {
            ApplyViewPreset("bottom");
        });

        CreateButton("도면검토", 410, -60, 90, 34, () =>
        {
            ApplyViewPreset("review");
        });


        // 3줄: 구조물
        CreateButton("PF", 20, -100, 55, 32, () =>
        {
            ToggleGroupSmart("PF_HPILE");
        });

        CreateButton("CIP", 85, -100, 55, 32, () =>
        {
            ToggleGroupSmart("CIP");
        });

        CreateButton("띠장", 150, -100, 65, 32, () =>
        {
            ToggleGroupSmart("WALE");
            ToggleGroupSmart("WALE_SPEC_REVIEW");
        });

        CreateButton("버팀", 225, -100, 65, 32, () =>
        {
            ToggleGroupSmart("STRUT_L1");
        });

        CreateButton("코너버팀", 300, -100, 85, 32, () =>
        {
            ToggleGroupSmart("CORNER_STRUT_L1");
        });

        CreateButton("앵커", 395, -100, 65, 32, () =>
        {
            ToggleGroupSmart("ANCHOR_L1");
        });

        CreateButton("높이자", 470, -100, 75, 32, () =>
        {
            if (builder != null)
                builder.ToggleElevationRuler();
        });

        CreateButton("PILE구간", 555, -100, 85, 32, () =>
        {
            ToggleGroupSmart("PILE_SECTION_MARKER");
        });

        CreateButton("PILE번호", 650, -100, 85, 32, () =>
        {
            if (builder != null)
                builder.TogglePostPileNumberMarkers();
        });


        // 4줄: 토공 / 지층 / 바닥 검토 보조
        CreateButton("굴착면", 20, -138, 75, 32, () =>
        {
            ToggleGroupSmart("EXCAVATION_FACE");
        });

        CreateButton("바닥", 105, -138, 60, 32, () =>
        {
            ToggleGroupSmart("EXCAVATION_BOTTOM");
        });

        CreateButton("흙채움", 175, -138, 75, 32, () =>
        {
            if (builder != null)
                builder.ToggleSoilRockLayerClean();
        });

        CreateButton("지층", 260, -138, 60, 32, () =>
        {
            ToggleGroupSmart("SOIL_ROCK_LAYER");
        });

        CreateButton("지층글씨", 330, -138, 85, 32, () =>
        {
            ToggleGroupSmart("SOIL_ROCK_TEXT");
        });

        CreateButton("EL글씨", 425, -138, 75, 32, () =>
        {
            ToggleGroupSmart("BOTTOM_EL_TEXT");
        });

        CreateButton("구간EL", 510, -138, 75, 32, () =>
        {
            ToggleGroupSmart("SECTION_EL_TEXT");
        });

        CreateButton("바닥구분", 595, -138, 85, 32, () =>
        {
            ToggleGroupSmart("BOTTOM_ZONE_LINE");
        });

        CreateButton("최종바닥", 690, -138, 85, 32, () =>
        {
            ToggleGroupSmart("FINAL_BOTTOM_STEP");
        });

        CreateButton("동자리", 785, -138, 75, 32, () =>
        {
            ToggleGroupSmart("PLAN_VECTOR_OVERLAY");
        });

        CreateSoilLegendUI();
    }
'''

text = text[:start] + new_block + text[end:]
path.write_text(text, encoding="utf-8")
print("버튼 CreateButton 영역 4줄 구조로 강제 재배치 완료")
