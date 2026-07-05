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

        string jsonPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Review", "post_pile_number_points_v1.json");

        if (!File.Exists(jsonPath))
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON 없음: " + jsonPath);
            return;
        }

        PostPileNumberPointRoot root = JsonUtility.FromJson<PostPileNumberPointRoot>(File.ReadAllText(jsonPath));

        if (root == null || root.points == null || root.points.Length == 0)
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON에 point 없음");
            return;
        }

        Bounds targetBounds;
        if (!TryGetPostPileNumberTargetBounds(out targetBounds))
        {
            targetBounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
            Debug.LogWarning("[POST_PILE_NUMBER] 기준 Bounds fallback 사용");
        }

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minY = float.MaxValue;
        float maxY = float.MinValue;

        foreach (var p in root.points)
        {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.y > maxY) maxY = p.y;
        }

        // PF 좌표 전체 범위에 약간 여유
        float padX = (maxX - minX) * 0.01f;
        float padY = (maxY - minY) * 0.01f;
        minX -= padX;
        maxX += padX;
        minY -= padY;
        maxY += padY;

        postPileNumberGroup = new GameObject("POST_PILE_NUMBER_MARKER");
        postPileNumberGroup.transform.SetParent(this.transform, false);

        Material discMat = CreatePostPileNumberDiscMaterial();
        Material outlineMat = CreatePostPileNumberOutlineMaterial();

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 120);

        int created = 0;

        foreach (var p in root.points)
        {
            if (p.no < 1 || p.no > 492)
                continue;

            // 전체 492개는 너무 촘촘하므로 우선 주요번호만 표시
            // P001, P010, P020 ... P490, P492
            bool showMajor =
                p.no == 1 ||
                p.no == 492 ||
                p.no % 10 == 0;

            if (!showMajor)
                continue;

            Vector3 pos = MapPostPilePointToWorld(p.x, p.y, minX, maxX, minY, maxY, targetBounds);
            CreatePostPileNumberMarker(postPileNumberGroup.transform, p.no, pos, discMat, outlineMat, font);
            created++;
        }

        postPileNumberGroup.SetActive(false);

        Debug.Log("[POST_PILE_NUMBER] JSON point count: " + root.points.Length);
        Debug.Log("[POST_PILE_NUMBER] 주요 포스트파일 번호 생성: " + created);
        Debug.Log("[POST_PILE_NUMBER] targetBounds center=" + targetBounds.center + " size=" + targetBounds.size);
    }
'''

new_bounds = r'''
    private bool TryGetPostPileNumberTargetBounds(out Bounds bounds)
    {
        // 번호는 바닥이 아니라 캡빔/PF/CIP 상단 외곽에 맞춰야 한다.
        // EXCAVATION_BOTTOM은 안쪽 바닥 기준이라 사용 우선순위를 낮춘다.
        string[] candidates = new string[]
        {
            "CIP",
            "PF",
            "PF_HPILE",
            "WALE_SPEC_REVIEW",
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
                Debug.Log("[POST_PILE_NUMBER] 기준 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
        Debug.LogWarning("[POST_PILE_NUMBER] 기준 Bounds fallback 사용");
        return true;
    }
'''

new_map = r'''
    private Vector3 MapPostPilePointToWorld(
        float srcX,
        float srcY,
        float minX,
        float maxX,
        float minY,
        float maxY,
        Bounds targetBounds)
    {
        // PF points[] 평균좌표는 DXF 원좌표이므로 targetBounds에 매핑한다.
        float nx = Mathf.InverseLerp(minX, maxX, srcX);
        float nz = Mathf.InverseLerp(minY, maxY, srcY);

        // 마진을 거의 두지 않아 캡빔 외곽에 가깝게 붙인다.
        float marginX = targetBounds.size.x * 0.004f;
        float marginZ = targetBounds.size.z * 0.004f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        Vector3 c = targetBounds.center;

        // 이전보다 바깥쪽으로 확장.
        // 번호가 안쪽에 생성되었으므로 1보다 크게 잡는다.
        float expand = 1.08f;
        x = c.x + (x - c.x) * expand;
        z = c.z + (z - c.z) * expand;

        // 캡빔 상단보다 확실히 위
        float y = targetBounds.max.y + 2.20f;

        return new Vector3(x, y, z);
    }
'''

new_marker = r'''
    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);
        root.transform.position = worldPos;
        root.transform.rotation = Quaternion.identity;

        Material whiteMat = CreatePostPileNumberDiscMaterial();
        Material blackMat = CreatePostPileNumberOutlineMaterial();

        // 흰색 원형판
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "PILE_NO_DISC_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = Vector3.zero;
        disc.transform.localScale = new Vector3(1.25f, 0.055f, 1.25f);

        Renderer dr = disc.GetComponent<Renderer>();
        if (dr != null)
        {
            dr.sharedMaterial = whiteMat;
            dr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            dr.receiveShadows = false;
        }

        Collider dc = disc.GetComponent<Collider>();
        if (dc != null) DestroyImmediate(dc);

        // 검정 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "PILE_NO_OUTLINE_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = new Vector3(0f, -0.04f, 0f);
        outline.transform.localScale = new Vector3(1.42f, 0.04f, 1.42f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = blackMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 번호 텍스트
        GameObject txtObj = new GameObject("PILE_NO_TEXT_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.16f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = "P" + no.ToString("000");
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 130;
        tm.characterSize = 0.062f;
        tm.color = Color.black;
        tm.richText = false;

        Font useFont = font;
        if (useFont == null)
            useFont = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 130);

        if (useFont != null)
        {
            tm.font = useFont;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(useFont.material);
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
text = replace_method(text, "private bool TryGetPostPileNumberTargetBounds", new_bounds)
text = replace_method(text, "private Vector3 MapPostPilePointToWorld", new_map)
text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

path.write_text(text, encoding="utf-8")
print("PILE번호 주요번호 방식 복구 + 캡빔 상단 보정 완료")
