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
        float nx = Mathf.InverseLerp(minX, maxX, srcX);
        float nz = Mathf.InverseLerp(minY, maxY, srcY);

        float marginX = targetBounds.size.x * 0.03f;
        float marginZ = targetBounds.size.z * 0.03f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 핵심 수정:
        // EXCAVATION_BOTTOM의 y는 너무 낮다.
        // 캡빔 상단 위로 고정 표시한다.
        float y = 8.50f;

        return new Vector3(x, y, z);
    }
'''

new_marker = r'''
    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);

        // MapPostPilePointToWorld에서 이미 캡빔 상단 높이로 계산했으므로 추가 Y 오프셋 금지
        root.transform.position = worldPos;
        root.transform.rotation = Quaternion.identity;

        Material whiteMat = CreatePostPileNumberDiscMaterial();
        Material blackMat = CreatePostPileNumberOutlineMaterial();

        // 흰 원형판
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "PILE_NO_DISC_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = Vector3.zero;
        disc.transform.localScale = new Vector3(1.15f, 0.055f, 1.15f);

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
        outline.transform.localScale = new Vector3(1.32f, 0.035f, 1.32f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = blackMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 숫자 텍스트: P365처럼 바닥 위에 눕혀 표시
        GameObject txtObj = new GameObject("PILE_NO_TEXT_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.16f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = no.ToString("000");
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 96;
        tm.characterSize = 0.065f;
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

new_disc_mat = r'''
    private Material CreatePostPileNumberDiscMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 1f, 1f);
        mat.renderQueue = 4500;
        return mat;
    }
'''

new_outline_mat = r'''
    private Material CreatePostPileNumberOutlineMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 4400;
        return mat;
    }
'''

text = replace_method(text, "private Vector3 MapPostPilePointToWorld", new_map)
text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)
text = replace_method(text, "private Material CreatePostPileNumberDiscMaterial", new_disc_mat)
text = replace_method(text, "private Material CreatePostPileNumberOutlineMaterial", new_outline_mat)

path.write_text(text, encoding="utf-8")
print("PILE번호 캡빔 상단 고정높이 원형 라벨 방식으로 수정 완료")
