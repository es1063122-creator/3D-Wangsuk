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


new_try_bounds = r'''
    private bool TryGetPostPileNumberTargetBounds(out Bounds bounds)
    {
        // 번호마커는 전체 3D 모델 기준으로 높이를 잡아야 한다.
        // EXCAVATION_BOTTOM은 y가 낮아서 캡빔 위 번호가 묻힌다.
        string[] candidates = new string[]
        {
            "Wangsuk_CAD_3D_ROOT",
            "PF",
            "PF_HPILE",
            "CIP",
            "PLAN_VECTOR_OVERLAY",
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
        // c605_pf_hpile.json 좌표가 이미 Unity 좌표인 경우가 많다.
        // 이 경우에는 다시 Bounds에 매핑하면 위치가 틀어진다.
        float x = srcX;
        float z = srcY;

        bool looksLikeUnityCoord =
            Mathf.Abs(srcX) < 2000f &&
            Mathf.Abs(srcY) < 2000f;

        if (!looksLikeUnityCoord)
        {
            // DXF 원좌표처럼 큰 값일 때만 fallback 매핑
            float nx = Mathf.InverseLerp(minX, maxX, srcX);
            float nz = Mathf.InverseLerp(minY, maxY, srcY);

            float marginX = targetBounds.size.x * 0.03f;
            float marginZ = targetBounds.size.z * 0.03f;

            x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
            z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);
        }

        // 전체 모델 상단보다 살짝 위.
        // C605 전체 Bounds 기준 max.y가 캡빔 상단에 가까움.
        float y = targetBounds.max.y + 0.85f;

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
        disc.transform.localScale = new Vector3(0.95f, 0.045f, 0.95f);

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
        outline.transform.localPosition = new Vector3(0f, -0.035f, 0f);
        outline.transform.localScale = new Vector3(1.08f, 0.035f, 1.08f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = blackMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 숫자: 캡빔 상단에서 위를 향하도록 눕힘
        GameObject txtObj = new GameObject("PILE_NO_TEXT_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.13f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = no.ToString("000");
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 96;
        tm.characterSize = 0.052f;
        tm.color = Color.black;
        tm.richText = false;

        Font useFont = font;
        if (useFont == null)
            useFont = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 96);

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

text = replace_method(text, "private bool TryGetPostPileNumberTargetBounds", new_try_bounds)
text = replace_method(text, "private Vector3 MapPostPilePointToWorld", new_map)
text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

path.write_text(text, encoding="utf-8")
print("PILE번호 좌표 직접사용 + 캡빔 상단 기준으로 수정 완료")
