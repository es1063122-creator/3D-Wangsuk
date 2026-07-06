using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

public class WangsukViewerUI : MonoBehaviour
{
    public WangsukFullModelBuilder builder;
    public ModelGroupRegistry registry;
    public WangsukFitView fitView;

    private Canvas canvas;

    private void Start()
    {
        if (builder == null) builder = FindObjectOfType<WangsukFullModelBuilder>();
        if (registry == null) registry = FindObjectOfType<ModelGroupRegistry>();
        if (fitView == null) fitView = FindObjectOfType<WangsukFitView>();

        if (fitView == null && Camera.main != null)
            fitView = Camera.main.gameObject.AddComponent<WangsukFitView>();

        EnsureEventSystem();
        CreateUI();
    }

    private void EnsureEventSystem()
    {
        if (FindObjectOfType<EventSystem>() != null)
            return;

        GameObject eventObj = new GameObject("EventSystem");
        eventObj.AddComponent<EventSystem>();
        eventObj.AddComponent<StandaloneInputModule>();
    }

    private void CreateUI()
    {
        GameObject canvasObj = new GameObject("Wangsuk_UI_Canvas");
        canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;

        CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);

        canvasObj.AddComponent<GraphicRaycaster>();

        // =========================
        // WebGL 공개용 UI 정리 버전
        // 1줄: 실행 / 뷰 / 프리셋
        // 2줄: 구조물
        // 3줄: 토공 / 지층 / 검토
        // =========================

        // ================================
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
            if (builder != null) builder.ScheduleCipTransparentApply();
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
            if (builder != null) builder.ScheduleCipTransparentApply();
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
            ToggleAnchorReview();
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
        CreatePublicTitleUI();

        // WebGL 공개용 자동 시작
        // 링크 접속 후 0.5초 뒤 모델 생성 + 기본보기 + 3D Fit 자동 실행
        Invoke(nameof(AutoBuildForPublicView), 0.5f);
    }




    
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

    // 우측 상단 범례와 겹치지 않도록 좌측 버튼 아래에 배치
    rt.anchorMin = new Vector2(0, 1);
    rt.anchorMax = new Vector2(0, 1);
    rt.pivot = new Vector2(0, 1);
    rt.anchoredPosition = new Vector2(20, -178);
    rt.sizeDelta = new Vector2(760, 58);

    Image bg = panel.AddComponent<Image>();
    bg.color = new Color(0.02f, 0.025f, 0.035f, 0.68f);

    GameObject titleObj = new GameObject("TitleText");
    titleObj.transform.SetParent(panel.transform, false);

    RectTransform titleRt = titleObj.AddComponent<RectTransform>();
    titleRt.anchorMin = new Vector2(0, 0.48f);
    titleRt.anchorMax = new Vector2(1, 1);
    titleRt.offsetMin = new Vector2(14, 0);
    titleRt.offsetMax = new Vector2(-14, -3);

    Text title = titleObj.AddComponent<Text>();
    title.text = "동진토건(주) 왕숙 A-6BL 흙막이 가시설 3D 검토 뷰어";
    title.alignment = TextAnchor.MiddleLeft;
    title.fontSize = 19;
    title.fontStyle = FontStyle.Bold;
    title.color = new Color(1f, 1f, 1f, 1f);
    title.font = KoreanFontProvider.Get();

    GameObject guideObj = new GameObject("GuideText");
    guideObj.transform.SetParent(panel.transform, false);

    RectTransform guideRt = guideObj.AddComponent<RectTransform>();
    guideRt.anchorMin = new Vector2(0, 0);
    guideRt.anchorMax = new Vector2(1, 0.48f);
    guideRt.offsetMin = new Vector2(14, 4);
    guideRt.offsetMax = new Vector2(-14, 0);

    Text guide = guideObj.AddComponent<Text>();
    guide.text = "마우스 드래그: 회전 / 휠: 확대·축소 / 우클릭 드래그: 이동";
    guide.alignment = TextAnchor.MiddleLeft;
    guide.fontSize = 13;
    guide.fontStyle = FontStyle.Normal;
    guide.color = new Color(0.78f, 0.88f, 1f, 1f);
    guide.font = KoreanFontProvider.Get();

    Debug.Log("[PUBLIC_TITLE] 공개용 제목 패널 생성 완료 - 좌측 배치");
}



    private void AutoBuildForPublicView()
    {
        if (builder == null)
            builder = FindObjectOfType<WangsukFullModelBuilder>();

        if (fitView == null)
            fitView = FindObjectOfType<WangsukFitView>();

        if (builder == null)
        {
            Debug.LogWarning("[PUBLIC_START] WangsukFullModelBuilder를 찾지 못했습니다.");
            return;
        }

        Debug.Log("[PUBLIC_START] WebGL 공개용 자동 모델 생성 시작");

        builder.BuildAll();

        ApplyViewPreset("basic");

        if (fitView != null)
            fitView.Fit3D();

        Debug.Log("[PUBLIC_START] 자동 생성 + 기본보기 + 3D뷰 적용 완료");
    }


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

    private void CreateButton(string text, float x, float y, float w, float h, UnityEngine.Events.UnityAction action)
    {
        GameObject btnObj = new GameObject("BTN_" + text);
        btnObj.transform.SetParent(canvas.transform, false);

        RectTransform rt = btnObj.AddComponent<RectTransform>();
        rt.anchorMin = new Vector2(0, 1);
        rt.anchorMax = new Vector2(0, 1);
        rt.pivot = new Vector2(0, 1);
        rt.anchoredPosition = new Vector2(x, y);
        rt.sizeDelta = new Vector2(w, h);

        Image img = btnObj.AddComponent<Image>();
        img.color = GetButtonColor(text);

        Button btn = btnObj.AddComponent<Button>();
        btn.targetGraphic = img;
        btn.onClick.AddListener(action);

        GameObject txtObj = new GameObject("Text");
        txtObj.transform.SetParent(btnObj.transform, false);

        RectTransform trt = txtObj.AddComponent<RectTransform>();
        trt.anchorMin = Vector2.zero;
        trt.anchorMax = Vector2.one;
        trt.offsetMin = Vector2.zero;
        trt.offsetMax = Vector2.zero;

        Text t = txtObj.AddComponent<Text>();
        t.text = text;
        t.font = KoreanFontProvider.Get();
        t.fontSize = 18;
        t.color = Color.white;
        t.alignment = TextAnchor.MiddleCenter;
        t.raycastTarget = false;
    }

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
        txt.fontStyle = FontStyle.Bold;
        txt.alignment = TextAnchor.MiddleLeft;

        Font font = KoreanFontProvider.Get();
        if (font == null)
            font = KoreanFontProvider.Get();

        txt.font = font;
    }



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


    private void ToggleGroupSmart(string groupName)
    {
GameObject target = null;

        // 비활성 오브젝트까지 찾기 위해 Resources.FindObjectsOfTypeAll 사용
        GameObject[] allObjects = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in allObjects)
        {
            if (go == null)
                continue;

            if (go.name != groupName)
                continue;

            // Project Asset이 아니라 실제 Scene 오브젝트만 사용
            if (!go.scene.IsValid())
                continue;

            target = go;
            break;
        }

        if (target != null)
        {
            target.SetActive(!target.activeSelf);
            Debug.Log("ToggleGroupSmart: " + groupName + " => " + target.activeSelf);
            return;
        }

        if (registry != null)
        {
            registry.ToggleGroup(groupName);
            Debug.Log("ToggleGroupSmart registry fallback: " + groupName);
        }
        else
        {
            Debug.LogWarning("ToggleGroupSmart 실패: 그룹을 찾지 못함 - " + groupName);
        }
    }


    
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


    public void OnClickFloorReviewInfo()
    {
        if (builder == null)
            builder = FindObjectOfType<WangsukFullModelBuilder>();

        if (builder != null)
            builder.ToggleFloorReviewInfoOverlay();
        else
            Debug.LogWarning("[UI] WangsukFullModelBuilder를 찾지 못했습니다.");
    }}



























