from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

preset_buttons = '''        CreateButton("기본보기", 20, -115, 90, 34, () =>
        {
            ApplyViewPreset("basic");
        });

        CreateButton("구조물", 120, -115, 80, 34, () =>
        {
            ApplyViewPreset("structure");
        });

        CreateButton("굴착지층", 210, -115, 90, 34, () =>
        {
            ApplyViewPreset("excavation");
        });

        CreateButton("바닥검토", 310, -115, 90, 34, () =>
        {
            ApplyViewPreset("bottom");
        });

        CreateButton("도면검토", 410, -115, 90, 34, () =>
        {
            ApplyViewPreset("review");
        });

        CreateButton("전체숨김", 510, -115, 90, 34, () =>
        {
            ApplyViewPreset("hide");
        });'''

if 'ApplyViewPreset("basic")' not in text:
    marker = "        CreateSoilLegendUI();"
    if marker in text:
        text = text.replace(marker, preset_buttons + "\n\n" + marker)
        print("보기 프리셋 버튼 추가 완료")
    else:
        print("CreateSoilLegendUI 기준 문구를 찾지 못했습니다.")
else:
    print("보기 프리셋 버튼 이미 있음")

helper = r'''
    private void ApplyViewPreset(string preset)
    {
        string[] allGroups = new string[]
        {
            "PF",
            "CIP",
            "WALE",
            "STRUT_L1",
            "CORNER_STRUT_L1",
            "ANCHOR_L1",
            "EXCAVATION_FACE",
            "EXCAVATION_BOTTOM",
            "SOIL_ROCK_LAYER",
            "SOIL_ROCK_TEXT",
            "SECTION_EL_TEXT",
            "PILE_SECTION_MARKER",
            "BOTTOM_ZONE_LINE",
            "PLAN_VECTOR_OVERLAY",
            "FINAL_BOTTOM_STEP",
            "PLAN_OVERLAY",
            "BOTTOM_EL_ZONE"
        };

        foreach (string g in allGroups)
            SetGroupActiveSmart(g, false);

        if (preset == "hide")
        {
            Debug.Log("보기 프리셋: 전체숨김");
            return;
        }

        if (preset == "basic")
        {
            SetManyGroupsActive(true,
                "PF",
                "CIP",
                "WALE",
                "STRUT_L1",
                "CORNER_STRUT_L1",
                "ANCHOR_L1",
                "EXCAVATION_FACE",
                "EXCAVATION_BOTTOM",
                "SOIL_ROCK_LAYER"
            );

            Debug.Log("보기 프리셋: 기본보기");
            return;
        }

        if (preset == "structure")
        {
            SetManyGroupsActive(true,
                "PF",
                "CIP",
                "WALE",
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
                "SOIL_ROCK_LAYER"
            );

            Debug.Log("보기 프리셋: 굴착지층");
            return;
        }

        if (preset == "bottom")
        {
            SetManyGroupsActive(true,
                "EXCAVATION_BOTTOM",
                "PLAN_VECTOR_OVERLAY",
                "FINAL_BOTTOM_STEP",
                "SECTION_EL_TEXT",
                "BOTTOM_ZONE_LINE"
            );

            Debug.Log("보기 프리셋: 바닥검토");
            return;
        }

        if (preset == "review")
        {
            SetManyGroupsActive(true,
                "PF",
                "CIP",
                "WALE",
                "STRUT_L1",
                "CORNER_STRUT_L1",
                "ANCHOR_L1",
                "EXCAVATION_FACE",
                "EXCAVATION_BOTTOM",
                "SOIL_ROCK_LAYER",
                "PLAN_VECTOR_OVERLAY",
                "SECTION_EL_TEXT",
                "PILE_SECTION_MARKER",
                "BOTTOM_ZONE_LINE"
            );

            Debug.Log("보기 프리셋: 도면검토");
            return;
        }

        Debug.LogWarning("알 수 없는 보기 프리셋: " + preset);
    }

    private void SetManyGroupsActive(bool active, params string[] groupNames)
    {
        foreach (string groupName in groupNames)
            SetGroupActiveSmart(groupName, active);
    }

    private void SetGroupActiveSmart(string groupName, bool active)
    {
        GameObject target = null;

        GameObject[] allObjects = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in allObjects)
        {
            if (go == null)
                continue;

            if (go.name != groupName)
                continue;

            if (!go.scene.IsValid())
                continue;

            target = go;
            break;
        }

        if (target != null)
        {
            target.SetActive(active);
            return;
        }

        // 없는 그룹은 조용히 넘어감.
        // 일부 그룹은 아직 생성 전이거나 현재 도면에 없는 경우가 있음.
    }
'''

if "private void ApplyViewPreset(string preset)" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("보기 프리셋 함수 추가 완료")
else:
    print("보기 프리셋 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
