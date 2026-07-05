from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

method = r'''

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

            // 높이 기준 계산에서 제외할 것들
            if (n.Contains("ELEVATION_RULER") || parentName.Contains("ELEVATION_RULER"))
                continue;

            // 앙카는 하향각 때문에 토공바닥보다 아래로 내려가므로 기준 계산에서 제외
            if (n.Contains("ANCHOR") || parentName.Contains("ANCHOR"))
                continue;

            // 글자/라벨은 실제 구조물 높이가 아니므로 제외
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

        float offset = Mathf.Max(5.0f, Mathf.Max(b.size.x, b.size.z) * 0.035f);

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

        Material poleMat = CreateElevationRulerMaterial(new Color(0.40f, 0.95f, 1.0f, 0.30f));
        Material tickMat = CreateElevationRulerMaterial(new Color(1.0f, 1.0f, 1.0f, 0.65f));
        Material zeroMat = CreateElevationRulerMaterial(new Color(1.0f, 0.35f, 0.10f, 0.80f));
        Material capMat = CreateElevationRulerMaterial(new Color(0.30f, 1.0f, 0.40f, 0.80f));

        for (int i = 0; i < positions.Length; i++)
        {
            BuildOneElevationRuler(group, positions[i], names[i], b.center, bottomY, topY, height, poleMat, tickMat, zeroMat, capMat);
        }

        group.SetActive(true);

        Debug.Log("========== ELEVATION_RULER 생성 ==========");
        Debug.Log("[ELEVATION_RULER] 토공바닥 기준 0m Y = " + bottomY);
        Debug.Log("[ELEVATION_RULER] 최상단 포스트/캡 Y = " + topY);
        Debug.Log("[ELEVATION_RULER] 표시 높이 = " + height + "m");
        Debug.Log("[ELEVATION_RULER] 1m 간격 눈금 / 외곽 4개소 생성 완료");
        Debug.Log("==========================================");
    }

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
        Material zeroMat,
        Material capMat)
    {
        GameObject holder = new GameObject("HEIGHT_RULER_" + label);
        holder.transform.SetParent(parent.transform, false);

        float poleRadius = 0.07f;

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

        Vector3 towardCenter = modelCenter - basePos;
        towardCenter.y = 0f;
        if (towardCenter.sqrMagnitude < 0.001f)
            towardCenter = Vector3.right;
        towardCenter.Normalize();

        int maxMeter = Mathf.CeilToInt(height);

        for (int m = 0; m <= maxMeter; m++)
        {
            float y = bottomY + m;
            if (y > topY + 0.01f)
                continue;

            bool isZero = m == 0;
            bool isFive = m % 5 == 0;
            bool isTopNear = Mathf.Abs(y - topY) < 0.2f;

            float tickLen = isZero ? 1.25f : (isFive ? 1.05f : 0.65f);
            float tickThickness = isZero ? 0.055f : (isFive ? 0.040f : 0.025f);

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

            if (isZero || isFive || m == maxMeter || isTopNear)
            {
                CreateElevationRulerText(
                    holder,
                    m.ToString() + "m",
                    new Vector3(basePos.x, y, basePos.z) + towardCenter * (tickLen + 0.65f),
                    0.32f,
                    isZero ? new Color(1.0f, 0.35f, 0.10f, 0.95f) : Color.white
                );
            }
            else
            {
                CreateElevationRulerText(
                    holder,
                    m.ToString() + "m",
                    new Vector3(basePos.x, y, basePos.z) + towardCenter * (tickLen + 0.45f),
                    0.22f,
                    new Color(1f, 1f, 1f, 0.80f)
                );
            }
        }

        // 최상단 캡 높이 별도 표시
        CreateElevationRulerText(
            holder,
            "CAP " + height.ToString("0.0") + "m",
            new Vector3(basePos.x, topY + 0.35f, basePos.z) + towardCenter * 1.65f,
            0.30f,
            new Color(0.30f, 1.0f, 0.40f, 0.95f)
        );

        GameObject topMarker = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        topMarker.name = "HEIGHT_CAP_MARKER_" + label;
        topMarker.transform.SetParent(holder.transform, false);
        topMarker.transform.position = new Vector3(basePos.x, topY, basePos.z);
        topMarker.transform.localScale = Vector3.one * 0.28f;

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

    private void CreateElevationRulerText(GameObject parent, string text, Vector3 pos, float size, Color color)
    {
        GameObject obj = new GameObject("HEIGHT_TEXT_" + text);
        obj.transform.SetParent(parent.transform, false);
        obj.transform.position = pos;

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = text;
        tm.fontSize = 96;
        tm.characterSize = size * 0.08f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = color;

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 96);
        if (font != null)
        {
            tm.font = font;
            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
                mr.sharedMaterial = font.material;
        }

        // 위에서 내려다보는 3D 검토 화면에 잘 보이도록 살짝 기울임
        obj.transform.rotation = Quaternion.Euler(65f, 0f, 0f);
    }

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

if "BuildElevationRulerFromModelBounds" not in text:
    marker = "    private void BuildAnchorSpecReviewFromPfCenters"
    idx = text.find(marker)
    if idx < 0:
        marker = "    private void BuildAnchorL1FromDxf"
        idx = text.find(marker)

    if idx < 0:
        raise SystemExit("높이 기준자 함수 삽입 위치를 찾지 못했습니다.")

    text = text[:idx] + method + "\n" + text[idx:]

# BuildSoilRockBandsAndLabels 이후에 높이 기준자 생성 호출 추가
if "BuildElevationRulerFromModelBounds();" not in text:
    pattern = r'(BuildSoilRockBandsAndLabels\s*\(\s*"c605_pf_hpile\.json"\s*\)\s*;)'
    text, count = re.subn(
        pattern,
        r'\1\n\n        // 토공바닥 0m 기준 / 최상단 포스트 캡까지 1m 간격 높이 기준자\n        BuildElevationRulerFromModelBounds();',
        text,
        count=1
    )

    if count == 0:
        raise SystemExit("BuildSoilRockBandsAndLabels 호출부를 찾지 못했습니다.")

path.write_text(text, encoding="utf-8")
print("ELEVATION_RULER 높이 기준자 함수 추가 및 호출 연결 완료")
