from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# CreateSoilLegendUI 호출 추가
if "CreateSoilLegendUI();" not in text:
    # 마지막 버튼 생성 뒤에 붙이기 위해 지층글씨 버튼 블록 기준 사용
    old = '''        CreateButton("지층글씨", 920, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("SOIL_ROCK_TEXT");
        });'''

    new = '''        CreateButton("지층글씨", 920, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("SOIL_ROCK_TEXT");
        });

        CreateSoilLegendUI();'''

    if old in text:
        text = text.replace(old, new)
        print("CreateSoilLegendUI 호출 추가 완료")
    else:
        print("지층글씨 버튼 기준 문구를 찾지 못했습니다. 다른 위치에 호출 추가 필요")
else:
    print("CreateSoilLegendUI 호출 이미 있음")

helper = r'''
    private void CreateSoilLegendUI()
    {
        GameObject panel = new GameObject("UI_SoilRockLegend");
        panel.transform.SetParent(canvas.transform, false);

        RectTransform rt = panel.AddComponent<RectTransform>();
        rt.anchorMin = new Vector2(1f, 1f);
        rt.anchorMax = new Vector2(1f, 1f);
        rt.pivot = new Vector2(1f, 1f);
        rt.anchoredPosition = new Vector2(-20f, -20f);
        rt.sizeDelta = new Vector2(250f, 185f);

        Image bg = panel.AddComponent<Image>();
        bg.color = new Color(0f, 0f, 0f, 0.62f);

        CreateLegendTitle(panel.transform, "지층 범례", 0, -18);
        CreateLegendRow(panel.transform, "매립층", new Color(0.45f, 0.25f, 0.08f, 0.85f), 0, -48);
        CreateLegendRow(panel.transform, "퇴적층", new Color(0.78f, 0.55f, 0.22f, 0.85f), 0, -76);
        CreateLegendRow(panel.transform, "풍화토", new Color(0.95f, 0.72f, 0.18f, 0.90f), 0, -104);
        CreateLegendRow(panel.transform, "풍화암", new Color(0.34f, 0.34f, 0.32f, 0.95f), 0, -132);
        CreateLegendText(panel.transform, "굴착저면 EL(+29.54~31.00)", 0, -162, 15);
    }

    private void CreateLegendTitle(Transform parent, string label, float x, float y)
    {
        CreateLegendText(parent, label, x, y, 17);
    }

    private void CreateLegendRow(Transform parent, string label, Color color, float x, float y)
    {
        GameObject box = new GameObject("LegendBox_" + label);
        box.transform.SetParent(parent, false);

        RectTransform brt = box.AddComponent<RectTransform>();
        brt.anchorMin = new Vector2(0f, 1f);
        brt.anchorMax = new Vector2(0f, 1f);
        brt.pivot = new Vector2(0f, 1f);
        brt.anchoredPosition = new Vector2(18f, y - 4f);
        brt.sizeDelta = new Vector2(34f, 18f);

        Image img = box.AddComponent<Image>();
        img.color = color;

        CreateLegendText(parent, label, 70f, y, 15);
    }

    private void CreateLegendText(Transform parent, string label, float x, float y, int fontSize)
    {
        GameObject obj = new GameObject("LegendText_" + label);
        obj.transform.SetParent(parent, false);

        RectTransform tr = obj.AddComponent<RectTransform>();
        tr.anchorMin = new Vector2(0f, 1f);
        tr.anchorMax = new Vector2(0f, 1f);
        tr.pivot = new Vector2(0f, 1f);
        tr.anchoredPosition = new Vector2(18f + x, y);
        tr.sizeDelta = new Vector2(220f, 26f);

        Text txt = obj.AddComponent<Text>();
        txt.text = label;
        txt.fontSize = fontSize;
        txt.color = Color.white;
        txt.alignment = TextAnchor.MiddleLeft;

        Font font = Font.CreateDynamicFontFromOSFont("Malgun Gothic", fontSize);
        if (font == null)
            font = Font.CreateDynamicFontFromOSFont("Arial", fontSize);

        txt.font = font;
    }
'''

if "private void CreateSoilLegendUI()" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("UI 지층 범례 함수 추가 완료")
else:
    print("UI 지층 범례 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
