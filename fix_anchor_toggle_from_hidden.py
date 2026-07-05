from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

old = '''        CreateButton("앵커", 395, -100, 65, 32, () =>
        {
            ToggleGroupSmart("ANCHOR_L1");
        });'''

new = '''        CreateButton("앵커", 395, -100, 65, 32, () =>
        {
            ToggleAnchorReview();
        });'''

if old not in text:
    raise SystemExit("앵커 버튼 기존 블록을 찾지 못했습니다. 좌표가 달라졌는지 확인 필요.")

text = text.replace(old, new, 1)

if "private void ToggleAnchorReview()" not in text:
    marker = "    private void ToggleGroupSmart(string groupName)"
    idx = text.find(marker)

    if idx < 0:
        raise SystemExit("ToggleGroupSmart 메서드 위치를 찾지 못했습니다.")

    method = r'''
    private void ToggleAnchorReview()
    {
        bool anyActive = IsGroupActiveSmart("ANCHOR_L1") ||
                         IsGroupActiveSmart("ANCHOR_L1_LEVEL") ||
                         IsGroupActiveSmart("ANCHOR_L2_LEVEL") ||
                         IsGroupActiveSmart("ANCHOR_L3_LEVEL");

        bool next = !anyActive;

        SetGroupActiveSmart("ANCHOR_L1", next);
        SetGroupActiveSmart("ANCHOR_L1_LEVEL", next);
        SetGroupActiveSmart("ANCHOR_L2_LEVEL", next);
        SetGroupActiveSmart("ANCHOR_L3_LEVEL", next);

        Debug.Log("ToggleAnchorReview: ANCHOR 전체 => " + next);
    }

    private bool IsGroupActiveSmart(string groupName)
    {
        GameObject[] allObjects = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in allObjects)
        {
            if (go == null) continue;
            if (go.name != groupName) continue;

            if (go.hideFlags != HideFlags.None)
                continue;

            return go.activeInHierarchy || go.activeSelf;
        }

        return false;
    }


'''
    text = text[:idx] + method + text[idx:]

path.write_text(text, encoding="utf-8")
print("앵커 전용 토글 함수 적용 완료")
