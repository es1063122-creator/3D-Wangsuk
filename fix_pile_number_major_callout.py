from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

def replace_method(src, signature, new_method):
    idx = src.find(signature)
    if idx < 0:
        raise SystemExit(f"메서드를 찾지 못했습니다: {signature}")

    brace = src.find("{", idx)
    if brace < 0:
        raise SystemExit(f"시작 중괄호를 찾지 못했습니다: {signature}")

    depth = 0
    end = -1

    for i in range(brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end < 0:
        raise SystemExit(f"끝 중괄호를 찾지 못했습니다: {signature}")

    return src[:idx] + new_method + src[end:]


new_build = r'''
    private void BuildPostPileNumberMarkers()
    {
        if (postPileNumberGroup != null)
        {
            DestroyImmediate(postPileNumberGroup);
            postPileNumberGroup = null;
        }

        postPileNumberGroup = new GameObject("POST_PILE_NUMBER_MARKER");
        postPileNumberGroup.transform.SetParent(this.transform, false);

        Bounds b;
        if (!TryGetPileMajorCalloutBounds(out b))
        {
            b = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
        }

        float y = b.max.y + 1.40f;

        // 도면 주요 PILE 번호 콜아웃.
        // 현재는 도면 이미지 기준 1차 배치값.
        // 위치가 보이면 X/Z만 미세 조정한다.
        CreatePileMajorCallout(postPileNumberGroup.transform, "P001", 0.93f, 0.92f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P067", 0.16f, 0.43f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P096", 0.10f, 0.57f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P114", 0.15f, 0.70f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P131", 0.25f, 0.90f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P365", 0.78f, 0.17f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P405", 0.60f, 0.12f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P428", 0.50f, 0.08f, b, y);
        CreatePileMajorCallout(postPileNumberGroup.transform, "P492", 0.35f, 0.05f, b, y);

        postPileNumberGroup.SetActive(false);

        Debug.Log("[POST_PILE_NUMBER] 주요 포스트파일 콜아웃 생성: 9");
        Debug.Log("[POST_PILE_NUMBER] 주요번호 기준 Bounds center=" + b.center + " size=" + b.size);
    }
'''

helpers = r'''

    private bool TryGetPileMajorCalloutBounds(out Bounds bounds)
    {
        // 도면/바닥 전체가 아니라 흙막이 상단 외곽을 기준으로 잡는다.
        string[] candidates = new string[]
        {
            "CIP",
            "PF",
            "PF_HPILE",
            "Wangsuk_CAD_3D_ROOT",
            "EXCAVATION_BOTTOM"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[POST_PILE_NUMBER] 주요번호 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }

    private void CreatePileMajorCallout(Transform parent, string label, float nx, float nz, Bounds b, float y)
    {
        float marginX = b.size.x * 0.04f;
        float marginZ = b.size.z * 0.04f;

        float x = Mathf.Lerp(b.min.x + marginX, b.max.x - marginX, nx);
        float z = Mathf.Lerp(b.min.z + marginZ, b.max.z - marginZ, nz);

        GameObject root = new GameObject("PILE_CALLOUT_" + label);
        root.transform.SetParent(parent, false);
        root.transform.position = new Vector3(x, y, z);

        Material whiteMat = CreatePostPileNumberDiscMaterial();
        Material blackMat = CreatePostPileNumberOutlineMaterial();

        // 원형 배경
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "CALLOUT_DISC_" + label;
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = Vector3.zero;
        disc.transform.localScale = new Vector3(2.2f, 0.06f, 2.2f);

        Renderer dr = disc.GetComponent<Renderer>();
        if (dr != null)
        {
            dr.sharedMaterial = whiteMat;
            dr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            dr.receiveShadows = false;
        }

        Collider dc = disc.GetComponent<Collider>();
        if (dc != null) DestroyImmediate(dc);

        // 검은 외곽
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "CALLOUT_OUTLINE_" + label;
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = new Vector3(0f, -0.04f, 0f);
        outline.transform.localScale = new Vector3(2.45f, 0.04f, 2.45f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = blackMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 텍스트
        GameObject txtObj = new GameObject("CALLOUT_TEXT_" + label);
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.18f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = label;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 120;
        tm.characterSize = 0.085f;
        tm.color = Color.black;
        tm.richText = false;

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 120);
        if (font != null)
        {
            tm.font = font;
            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.black;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }
'''

text = replace_method(text, "private void BuildPostPileNumberMarkers()", new_build)

if "private void CreatePileMajorCallout" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreatePostPileNumberDiscMaterial 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("PILE번호 주요 콜아웃 방식으로 전면 수정 완료")
