from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 1) UI 생성부에 제목 호출 추가
target = '''        CreateSoilLegendUI();

        // WebGL 공개용 자동 시작'''

replace = '''        CreateSoilLegendUI();
        CreatePublicTitleUI();

        // WebGL 공개용 자동 시작'''

if "CreatePublicTitleUI();" not in text:
    if target not in text:
        raise SystemExit("CreateSoilLegendUI() 위치를 찾지 못했습니다.")
    text = text.replace(target, replace, 1)

# 2) 제목 UI 메서드 추가
if "private void CreatePublicTitleUI()" not in text:
    marker = "    private void AutoBuildForPublicView()"
    idx = text.find(marker)

    if idx < 0:
        marker = "    private Color GetButtonColor"
        idx = text.find(marker)

    if idx < 0:
        marker = "    private void CreateButton"
        idx = text.find(marker)

    if idx < 0:
        raise SystemExit("메서드 삽입 위치를 찾지 못했습니다.")

    method = r'''
    private void CreatePublicTitleUI()
    {
        if (canvas == null)
            return;

        GameObject old = GameObject.Find("PUBLIC_TITLE_PANEL");
        if (old != null)
            DestroyImmediate(old);

        GameObject panel = new GameObject("PUBLIC_TITLE_PANEL");
        panel.transform.SetParent(canvas.transform, false);

        RectTransform rt = panel.AddComponent<RectTransform>();
        rt.anchorMin = new Vector2(1, 1);
        rt.anchorMax = new Vector2(1, 1);
        rt.pivot = new Vector2(1, 1);
        rt.anchoredPosition = new Vector2(-20, -20);
        rt.sizeDelta = new Vector2(690, 64);

        Image bg = panel.AddComponent<Image>();
        bg.color = new Color(0.02f, 0.025f, 0.035f, 0.72f);

        GameObject titleObj = new GameObject("TitleText");
        titleObj.transform.SetParent(panel.transform, false);

        RectTransform titleRt = titleObj.AddComponent<RectTransform>();
        titleRt.anchorMin = new Vector2(0, 0.48f);
        titleRt.anchorMax = new Vector2(1, 1);
        titleRt.offsetMin = new Vector2(14, 0);
        titleRt.offsetMax = new Vector2(-14, -4);

        Text title = titleObj.AddComponent<Text>();
        title.text = "동진토건(주) 왕숙 A-6BL 흙막이 가시설 3D 검토 뷰어";
        title.alignment = TextAnchor.MiddleRight;
        title.fontSize = 20;
        title.fontStyle = FontStyle.Bold;
        title.color = new Color(1f, 1f, 1f, 1f);
        title.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        GameObject guideObj = new GameObject("GuideText");
        guideObj.transform.SetParent(panel.transform, false);

        RectTransform guideRt = guideObj.AddComponent<RectTransform>();
        guideRt.anchorMin = new Vector2(0, 0);
        guideRt.anchorMax = new Vector2(1, 0.48f);
        guideRt.offsetMin = new Vector2(14, 4);
        guideRt.offsetMax = new Vector2(-14, 0);

        Text guide = guideObj.AddComponent<Text>();
        guide.text = "마우스 드래그: 회전 / 휠: 확대·축소 / 우클릭 드래그: 이동";
        guide.alignment = TextAnchor.MiddleRight;
        guide.fontSize = 14;
        guide.fontStyle = FontStyle.Normal;
        guide.color = new Color(0.78f, 0.88f, 1f, 1f);
        guide.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        Debug.Log("[PUBLIC_TITLE] 공개용 제목 패널 생성 완료");
    }


'''
    text = text[:idx] + method + text[idx:]

path.write_text(text, encoding="utf-8")
print("공개용 제목 패널 추가 완료")
