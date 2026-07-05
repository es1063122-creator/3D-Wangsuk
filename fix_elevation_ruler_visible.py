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
    private void BuildElevationRulerFromModelBounds()
    {
        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
        {
            Debug.LogWarning("[ELEVATION_RULER] Wangsuk_CAD_3D_ROOT 없음");
            return;
        }

        GameObject group = GameObject.Find("ELEVATION_RULER");
        if (group == null)
        {
            group = new GameObject("ELEVATION_RULER");
            group.transform.SetParent(root.transform, false);
        }

        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);

        bool hasBounds = false;
        Bounds b = new Bounds(Vector3.zero, Vector3.zero);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            string n = r.gameObject.name.ToUpper();
            string parentName = r.transform.parent != null ? r.transform.parent.name.ToUpper() : "";

            if (n.Contains("ELEVATION_RULER") || parentName.Contains("ELEVATION_RULER"))
                continue;

            if (n.Contains("ANCHOR") || parentName.Contains("ANCHOR"))
                continue;

            if (r.GetComponent<TextMesh>() != null)
                continue;

            if (n.Contains("TEXT") || n.Contains("LABEL") || n.Contains("PILE_NO") || n.Contains("EL_"))
                continue;

            if (!hasBounds)
            {
                b = r.bounds;
                hasBounds = true;
            }
            else
            {
                b.Encapsulate(r.bounds);
            }
        }

        if (!hasBounds)
        {
            Debug.LogWarning("[ELEVATION_RULER] Bounds 계산 실패");
            return;
        }

        float bottomY = b.min.y;
        float topY = b.max.y;
        float height = topY - bottomY;

        if (height <= 0.1f)
        {
            Debug.LogWarning("[ELEVATION_RULER] 높이 계산값 이상: " + height);
            return;
        }

        // 기존보다 훨씬 바깥으로 이동해서 모델과 겹치지 않게 함
        float offset = Mathf.Max(14.0f, Mathf.Max(b.size.x, b.size.z) * 0.085f);

        Vector3[] positions = new Vector3[]
        {
            new Vector3(b.min.x - offset, bottomY, b.min.z - offset),
            new Vector3(b.max.x + offset, bottomY, b.min.z - offset),
            new Vector3(b.min.x - offset, bottomY, b.max.z + offset),
            new Vector3(b.max.x + offset, bottomY, b.max.z + offset)
        };

        string[] names = new string[]
        {
            "LEFT_BOTTOM",
            "RIGHT_BOTTOM",
            "LEFT_TOP",
            "RIGHT_TOP"
        };

        Material poleMat = CreateElevationRulerOpaqueMaterial(Color.white);
        Material tickMat = CreateElevationRulerOpaqueMaterial(Color.black);
        Material boardMat = CreateElevationRulerOpaqueMaterial(Color.white);
        Material zeroMat = CreateElevationRulerOpaqueMaterial(new Color(1.0f, 0.05f, 0.02f, 1f));
        Material capMat = CreateElevationRulerOpaqueMaterial(new Color(0.00f, 0.65f, 0.20f, 1f));

        for (int i = 0; i < positions.Length; i++)
        {
            BuildOneElevationRuler(group, positions[i], names[i], b.center, bottomY, topY, height, poleMat, tickMat, boardMat, zeroMat, capMat);
        }

        group.SetActive(true);

        Debug.Log("========== ELEVATION_RULER 생성 ==========");
        Debug.Log("[ELEVATION_RULER] 모델 Bounds min = " + b.min + " / max = " + b.max);
        Debug.Log("[ELEVATION_RULER] 외곽 offset = " + offset);
        Debug.Log("[ELEVATION_RULER] 토공바닥 기준 0m Y = " + bottomY);
        Debug.Log("[ELEVATION_RULER] 최상단 포스트/캡 Y = " + topY);
        Debug.Log("[ELEVATION_RULER] 표시 높이 = " + height + "m");
        Debug.Log("[ELEVATION_RULER] 흰색 기준자/흰색 글씨판/검정 글씨 적용 완료");
        Debug.Log("==========================================");
    }
'''

new_one = r'''
    private void BuildOneElevationRuler(
        GameObject parent,
        Vector3 basePos,
        string label,
        Vector3 modelCenter,
        float bottomY,
        float topY,
        float height,
        Material poleMat,
        Material tickMat,
        Material boardMat,
        Material zeroMat,
        Material capMat)
    {
        GameObject holder = new GameObject("HEIGHT_RULER_" + label);
        holder.transform.SetParent(parent.transform, false);

        Vector3 towardCenter = modelCenter - basePos;
        towardCenter.y = 0f;
        if (towardCenter.sqrMagnitude < 0.001f)
            towardCenter = Vector3.right;
        towardCenter.Normalize();

        // 수직 흰색 기준봉
        float poleRadius = 0.12f;

        GameObject pole = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        pole.name = "HEIGHT_POLE_" + label;
        pole.transform.SetParent(holder.transform, false);
        pole.transform.position = new Vector3(basePos.x, bottomY + height * 0.5f, basePos.z);
        pole.transform.localScale = new Vector3(poleRadius, height * 0.5f, poleRadius);

        Renderer pr = pole.GetComponent<Renderer>();
        if (pr != null)
        {
            pr.sharedMaterial = poleMat;
            pr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            pr.receiveShadows = false;
        }

        Collider pc = pole.GetComponent<Collider>();
        if (pc != null)
            DestroyImmediate(pc);

        int maxMeter = Mathf.CeilToInt(height);

        // 전체 라벨용 흰색 배경판: 검정글씨가 잘 보이게
        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "HEIGHT_WHITE_BOARD_" + label;
        board.transform.SetParent(holder.transform, false);
        board.transform.position = new Vector3(basePos.x, bottomY + height * 0.5f, basePos.z) + towardCenter * 1.85f;
        board.transform.localScale = new Vector3(2.15f, height + 1.25f, 0.055f);
        board.transform.rotation = Quaternion.LookRotation(towardCenter, Vector3.up);

        Renderer br = board.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = boardMat;
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = board.GetComponent<Collider>();
        if (bc != null)
            DestroyImmediate(bc);

        for (int m = 0; m <= maxMeter; m++)
        {
            float y = bottomY + m;
            if (y > topY + 0.01f)
                continue;

            bool isZero = m == 0;
            bool isFive = m % 5 == 0;

            float tickLen = isZero ? 1.45f : (isFive ? 1.20f : 0.75f);
            float tickThickness = isZero ? 0.070f : (isFive ? 0.055f : 0.035f);

            GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tick.name = "HEIGHT_TICK_" + m.ToString("00") + "m_" + label;
            tick.transform.SetParent(holder.transform, false);
            tick.transform.position = new Vector3(basePos.x, y, basePos.z) + towardCenter * (tickLen * 0.5f);
            tick.transform.localScale = new Vector3(tickLen, tickThickness, tickThickness);
            tick.transform.rotation = Quaternion.FromToRotation(Vector3.right, towardCenter);

            Renderer tr = tick.GetComponent<Renderer>();
            if (tr != null)
            {
                tr.sharedMaterial = isZero ? zeroMat : tickMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }

            Collider tc = tick.GetComponent<Collider>();
            if (tc != null)
                DestroyImmediate(tc);

            // 모든 1m 라벨 표시
            Color textColor = isZero ? new Color(1.0f, 0.0f, 0.0f, 1f) : Color.black;
            float textSize = isZero || isFive ? 0.36f : 0.28f;

            CreateElevationRulerText(
                holder,
                m.ToString() + "m",
                new Vector3(basePos.x, y, basePos.z) + towardCenter * 2.00f,
                modelCenter,
                textSize,
                textColor
            );
        }

        // 최상단 표시
        CreateElevationRulerText(
            holder,
            "CAP " + height.ToString("0.0") + "m",
            new Vector3(basePos.x, topY + 0.45f, basePos.z) + towardCenter * 2.00f,
            modelCenter,
            0.34f,
            new Color(0.00f, 0.55f, 0.15f, 1f)
        );

        GameObject topMarker = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        topMarker.name = "HEIGHT_CAP_MARKER_" + label;
        topMarker.transform.SetParent(holder.transform, false);
        topMarker.transform.position = new Vector3(basePos.x, topY, basePos.z);
        topMarker.transform.localScale = Vector3.one * 0.38f;

        Renderer mr = topMarker.GetComponent<Renderer>();
        if (mr != null)
        {
            mr.sharedMaterial = capMat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }

        Collider mc = topMarker.GetComponent<Collider>();
        if (mc != null)
            DestroyImmediate(mc);
    }
'''

new_text = r'''
    private void CreateElevationRulerText(GameObject parent, string text, Vector3 pos, Vector3 modelCenter, float size, Color color)
    {
        GameObject obj = new GameObject("HEIGHT_TEXT_" + text);
        obj.transform.SetParent(parent.transform, false);
        obj.transform.position = pos;

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = text;
        tm.fontSize = 120;
        tm.characterSize = size * 0.10f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = color;
        tm.richText = false;

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 120);
        if (font != null)
        {
            tm.font = font;
            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.sharedMaterial = font.material;
                mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                mr.receiveShadows = false;
            }
        }

        Vector3 faceDir = pos - modelCenter;
        faceDir.y = 0f;
        if (faceDir.sqrMagnitude < 0.001f)
            faceDir = Vector3.forward;

        // 외곽에 세운 글씨가 모델 중심을 향하도록 회전
        obj.transform.rotation = Quaternion.LookRotation(faceDir.normalized, Vector3.up);
    }
'''

new_opaque_mat = r'''
    private Material CreateElevationRulerOpaqueMaterial(Color color)
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;
        mat.SetFloat("_Glossiness", 0f);
        return mat;
    }
'''

new_trans_mat = r'''
    private Material CreateElevationRulerMaterial(Color color)
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

        mat.renderQueue = 3300;
        return mat;
    }
'''

text = replace_method(text, "private void BuildElevationRulerFromModelBounds", new_build)
text = replace_method(text, "private void BuildOneElevationRuler", new_one)
text = replace_method(text, "private void CreateElevationRulerText", new_text)

if "private Material CreateElevationRulerOpaqueMaterial" not in text:
    marker = "    private Material CreateElevationRulerMaterial"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreateElevationRulerMaterial 위치를 찾지 못했습니다.")
    text = text[:idx] + new_opaque_mat + "\n" + text[idx:]

# 기존 투명 재질 함수는 유지하되, 혹시 깨졌으면 정상화
text = replace_method(text, "private Material CreateElevationRulerMaterial", new_trans_mat)

path.write_text(text, encoding="utf-8")
print("높이 기준자 시인성 개선 완료: 외곽 이동 + 흰색판 + 검정글씨")
