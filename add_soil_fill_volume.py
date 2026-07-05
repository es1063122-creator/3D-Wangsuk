from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

method = r'''

    private GameObject soilFillVolumeGroup;

    private void BuildSoilFillVolume()
    {
        if (soilFillVolumeGroup != null)
        {
            DestroyImmediate(soilFillVolumeGroup);
            soilFillVolumeGroup = null;
        }

        Bounds b;
        if (!TryGetSoilFillTargetBounds(out b))
        {
            Debug.LogWarning("[SOIL_FILL_VOLUME] 기준 Bounds를 찾지 못했습니다.");
            return;
        }

        soilFillVolumeGroup = new GameObject("SOIL_FILL_VOLUME");
        soilFillVolumeGroup.transform.SetParent(this.transform, false);

        // 굴착 내부 쪽으로 약간 축소해서 흙막이 벽/캡빔과 겹침을 줄임
        float innerScaleX = 0.82f;
        float innerScaleZ = 0.82f;

        float sx = b.size.x * innerScaleX;
        float sz = b.size.z * innerScaleZ;

        Vector3 center = b.center;

        // 전체 깊이 기준.
        // 현재 모델에서 top은 지표/상부, bottom은 굴착저면에 가까움.
        float topY = b.max.y - 0.40f;
        float bottomY = b.min.y + 0.40f;

        // 만약 EXCAVATION_BOTTOM만 잡혀서 y 두께가 거의 없으면 전체 모델 기준 fallback
        if (Mathf.Abs(topY - bottomY) < 1.0f)
        {
            topY = 4.5f;
            bottomY = -20.0f;
        }

        // 레벨별 두께 비율
        // 위에서 아래 방향
        float totalDepth = Mathf.Abs(topY - bottomY);

        float y0 = topY;
        float y1 = topY - totalDepth * 0.22f;
        float y2 = topY - totalDepth * 0.48f;
        float y3 = topY - totalDepth * 0.72f;
        float y4 = bottomY;

        CreateSoilFillLayer("매립층", center.x, center.z, sx, sz, y0, y1, new Color(0.62f, 0.36f, 0.14f, 0.28f));
        CreateSoilFillLayer("퇴적층", center.x, center.z, sx, sz, y1, y2, new Color(0.86f, 0.55f, 0.18f, 0.25f));
        CreateSoilFillLayer("풍화토", center.x, center.z, sx, sz, y2, y3, new Color(0.95f, 0.76f, 0.18f, 0.22f));
        CreateSoilFillLayer("풍화암", center.x, center.z, sx, sz, y3, y4, new Color(0.46f, 0.46f, 0.46f, 0.24f));

        soilFillVolumeGroup.SetActive(false);

        Debug.Log("[SOIL_FILL_VOLUME] 반투명 흙채움 생성 완료 / Bounds center=" + b.center + " size=" + b.size);
    }

    private bool TryGetSoilFillTargetBounds(out Bounds bounds)
    {
        // 굴착 내부 채움은 최종바닥/굴착바닥 기준으로 잡는 게 가장 안정적
        string[] candidates = new string[]
        {
            "FINAL_BOTTOM_STEP",
            "EXCAVATION_BOTTOM",
            "BOTTOM_ZONE_LINE",
            "PLAN_VECTOR_OVERLAY",
            "Wangsuk_CAD_3D_ROOT"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[SOIL_FILL_VOLUME] 기준 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }

    private void CreateSoilFillLayer(string layerName, float cx, float cz, float sx, float sz, float topY, float bottomY, Color color)
    {
        float h = Mathf.Abs(topY - bottomY);
        float cy = (topY + bottomY) * 0.5f;

        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "SOIL_FILL_" + layerName;
        go.transform.SetParent(soilFillVolumeGroup.transform, false);
        go.transform.position = new Vector3(cx, cy, cz);
        go.transform.localScale = new Vector3(sx, h, sz);

        Renderer r = go.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = CreateSoilFillTransparentMaterial(color);
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = go.GetComponent<Collider>();
        if (c != null) DestroyImmediate(c);

        // 레벨명 라벨
        CreateSoilFillLayerLabel(layerName, cx, topY + 0.15f, cz, color);
    }

    private void CreateSoilFillLayerLabel(string label, float x, float y, float z, Color color)
    {
        GameObject labelRoot = new GameObject("SOIL_FILL_LABEL_" + label);
        labelRoot.transform.SetParent(soilFillVolumeGroup.transform, false);
        labelRoot.transform.position = new Vector3(x, y, z);

        GameObject bg = GameObject.CreatePrimitive(PrimitiveType.Cube);
        bg.name = "LABEL_BG_" + label;
        bg.transform.SetParent(labelRoot.transform, false);
        bg.transform.localPosition = Vector3.zero;
        bg.transform.localScale = new Vector3(8.0f, 0.06f, 2.2f);

        Color bgColor = new Color(color.r, color.g, color.b, 0.72f);

        Renderer br = bg.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = CreateSoilFillTransparentMaterial(bgColor);
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = bg.GetComponent<Collider>();
        if (bc != null) DestroyImmediate(bc);

        GameObject txtObj = new GameObject("LABEL_TEXT_" + label);
        txtObj.transform.SetParent(labelRoot.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.12f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = label;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 100;
        tm.characterSize = 0.075f;
        tm.color = Color.white;
        tm.richText = false;

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Malgun Gothic", "맑은 고딕", "Arial" }, 100);
        if (font != null)
        {
            tm.font = font;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.white;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }

    private Material CreateSoilFillTransparentMaterial(Color color)
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;

        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);

        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");

        mat.renderQueue = 3100;
        return mat;
    }

    public void SetSoilFillVolume(bool active)
    {
        if (soilFillVolumeGroup == null)
            BuildSoilFillVolume();

        if (soilFillVolumeGroup != null)
        {
            soilFillVolumeGroup.SetActive(active);
            Debug.Log("[SOIL_FILL_VOLUME] 표시 상태: " + active);
        }
    }

    public void ToggleSoilFillVolume()
    {
        if (soilFillVolumeGroup == null)
            BuildSoilFillVolume();

        if (soilFillVolumeGroup != null)
            soilFillVolumeGroup.SetActive(!soilFillVolumeGroup.activeSelf);
    }

'''

if "BuildSoilFillVolume" not in text:
    marker = "    private Color ParseHtmlColor"
    idx = text.find(marker)

    if idx < 0:
        marker = "    private Material CreatePostPileNumberDiscMaterial"
        idx = text.find(marker)

    if idx < 0:
        raise SystemExit("삽입 위치를 찾지 못했습니다.")

    text = text[:idx] + method + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("SOIL_FILL_VOLUME 흙채움 기능 추가 완료")
