from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

signature = "private void ApplyViewPreset(string preset)"
start = text.find(signature)
if start < 0:
    raise SystemExit("ApplyViewPreset 메서드를 찾지 못했습니다.")

brace = text.find("{", start)
if brace < 0:
    raise SystemExit("ApplyViewPreset 시작 중괄호를 찾지 못했습니다.")

depth = 0
end = -1

for i in range(brace, len(text)):
    if text[i] == "{":
        depth += 1
    elif text[i] == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end < 0:
    raise SystemExit("ApplyViewPreset 끝 중괄호를 찾지 못했습니다.")

new_method = r'''
private void ApplyViewPreset(string preset)
{
    string[] allGroups = new string[]
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
    };

    // 먼저 전체 숨김으로 시작
    foreach (string g in allGroups)
        SetGroupActiveSmart(g, false);

    if (builder != null)
        builder.SetFloorReviewInfoOverlay(false);

    if (preset == "hide")
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
    }

    if (preset == "basic")
    {
        SetManyGroupsActive(true,
            "PF",
            "PF_HPILE",
            "CIP",
            "WALE",
            "WALE_SPEC_REVIEW",
            "ANCHOR_L1",
            "EXCAVATION_FACE",
            "EXCAVATION_BOTTOM"
        );

        Debug.Log("보기 프리셋: 기본보기");
        return;
    }

    if (preset == "structure")
    {
        SetManyGroupsActive(true,
            "PF",
            "PF_HPILE",
            "CIP",
            "WALE",
            "WALE_SPEC_REVIEW",
            "STRUT_L1",
            "CORNER_STRUT_L1",
            "ANCHOR_L1"
        );

        Debug.Log("보기 프리셋: 구조물");
        return;
    }

    if (preset == "excavation")
    {
        SetManyGroupsActive(true,
            "EXCAVATION_FACE",
            "EXCAVATION_BOTTOM",
            "SOIL_ROCK_LAYER",
            "SOIL_ROCK_TEXT",
            "SOIL_FILL_VOLUME"
        );

        Debug.Log("보기 프리셋: 굴착지층");
        return;
    }

    if (preset == "bottom")
    {
        SetManyGroupsActive(true,
            "EXCAVATION_BOTTOM",
            "FINAL_BOTTOM_STEP",
            "BOTTOM_ZONE_LINE",
            "SECTION_EL_TEXT",
            "BOTTOM_EL_TEXT",
            "PLAN_VECTOR_OVERLAY",
            "FLOOR_REVIEW_INFO"
        );

        if (builder != null)
            builder.SetFloorReviewInfoOverlay(true);

        Debug.Log("보기 프리셋: 바닥검토");
        return;
    }

    if (preset == "review")
    {
        SetManyGroupsActive(true,
            "PF",
            "PF_HPILE",
            "CIP",
            "WALE",
            "WALE_SPEC_REVIEW",
            "ANCHOR_L1",
            "PILE_SECTION_MARKER",
            "PILE_NUMBER_MARKER",
            "BOTTOM_ZONE_LINE",
            "SECTION_EL_TEXT",
            "BOTTOM_EL_TEXT",
            "ELEVATION_RULER"
        );

        Debug.Log("보기 프리셋: 도면검토");
        return;
    }

    Debug.LogWarning("알 수 없는 보기 프리셋: " + preset);
}
'''

text = text[:start] + new_method + text[end:]
path.write_text(text, encoding="utf-8")

print("ApplyViewPreset 프리셋 기능 정리 완료")
