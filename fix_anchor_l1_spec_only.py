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


new_build_anchor = r'''
    private void BuildAnchorL1FromDxf(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("C605 ANCHOR JSON 없음 또는 비어 있음: " + fileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup(groupKey);
        if (group == null)
        {
            group = new GameObject(groupKey);
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning(groupKey + " 그룹이 없어 강제 생성했습니다.");
        }

        // 재생성 시 기존 앙카 중복 제거
        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        List<Vector3> pfCentersForAnchor = LoadPfCentersForAnchorHead();

        int createdL1 = 0;
        int skipped = 0;

        // 띠장 수정 후 기준:
        // 1단 앙카는 도면기준 1단 띠장 높이에 맞춘다.
        // 기존 자동 L2/L3는 도면 근거가 부족하므로 생성하지 않는다.
        float anchorY = -1.00f;

        try
        {
            anchorY = -GetWaleSpecDepthByBand(1);
        }
        catch
        {
            anchorY = -1.00f;
        }

        foreach (var e in data.entities)
        {
            int made = CreateAnchorPolyline(group, e, anchorY, "ANCHOR_L1_SPEC", pfCentersForAnchor);
            if (made > 0)
                createdL1 += made;
            else
                skipped++;
        }

        Debug.Log("========== ANCHOR 도면기준 1차 보정 ==========");
        Debug.Log("ANCHOR_L1_SPEC 생성: " + createdL1);
        Debug.Log("ANCHOR 제외/스킵: " + skipped);
        Debug.Log("기준: 수정된 1단 띠장 높이에 맞춤. 기존 L2/L3 자동 생성 중지.");
        Debug.Log("주의: C-612~C-619 전개도 앵커 구간 정밀 대조 전 1차 보정값.");
        Debug.Log("==============================================");
    }
'''

new_create_anchor = r'''
    private int CreateAnchorPolyline(GameObject group, WangsukDxfEntity e, float y, string label, List<Vector3> pfCenters)
    {
        List<Vector3> pts = ConvertEntityPoints(e, y);
        if (pts == null || pts.Count < 2)
            return 0;

        Vector3 p0 = pts[0];
        Vector3 p1 = pts[pts.Count - 1];

        Vector3 anchorHead = p0;
        Vector3 anchorTail = p1;

        // PF/CIP 벽체에 가까운 끝점을 앙카 머리점으로 사용
        if (pfCenters != null && pfCenters.Count > 0)
        {
            float p0Dist = GetNearestDistanceXZ(p0, pfCenters);
            float p1Dist = GetNearestDistanceXZ(p1, pfCenters);

            if (p1Dist < p0Dist)
            {
                anchorHead = p1;
                anchorTail = p0;
            }

            float headDistSq = GetNearestDistanceXZ(anchorHead, pfCenters);

            // C-605 ANCHOR 레이어에는 도면 기호/외곽선도 섞일 수 있으므로,
            // PF/CIP에서 너무 먼 것은 제외
            if (headDistSq > 400f)
                return 0;
        }

        Vector3 dir = anchorTail - anchorHead;
        dir.y = 0f;

        float originalLen = dir.magnitude;
        if (originalLen < 0.10f)
            return 0;

        dir.Normalize();

        // 실제 앙카 대표 길이: 기존 검토값 12.28m 유지
        float displayLen = Mathf.Min(originalLen, 12.28f);
        if (displayLen < 4.0f)
            return 0;

        // 하향각 15도 유지
        float downwardAngleDeg = 15.0f;
        float downwardRad = downwardAngleDeg * Mathf.Deg2Rad;

        Vector3 slopedDir = dir * Mathf.Cos(downwardRad) + Vector3.down * Mathf.Sin(downwardRad);
        slopedDir.Normalize();

        Vector3 a = new Vector3(anchorHead.x, y, anchorHead.z);
        Vector3 b = a + slopedDir * displayLen;

        GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        anchor.name = "C605_" + label;
        anchor.transform.SetParent(group.transform, false);
        anchor.transform.position = (a + b) * 0.5f;
        anchor.transform.localScale = new Vector3(0.10f, 0.10f, displayLen);
        anchor.transform.rotation = Quaternion.LookRotation(slopedDir, Vector3.up);

        Renderer r = anchor.GetComponent<Renderer>();
        if (r != null)
        {
            Material mat = new Material(Shader.Find("Standard"));
            mat.color = new Color(0.75f, 1.0f, 0.10f, 1f);
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = anchor.GetComponent<Collider>();
        if (c != null)
            DestroyImmediate(c);

        // 머리점 표시: 띠장 접점 확인용
        GameObject head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        head.name = "ANCHOR_HEAD_" + label;
        head.transform.SetParent(group.transform, false);
        head.transform.position = a;
        head.transform.localScale = Vector3.one * 0.35f;

        Renderer hr = head.GetComponent<Renderer>();
        if (hr != null)
        {
            Material hm = new Material(Shader.Find("Standard"));
            hm.color = new Color(1.0f, 0.2f, 0.05f, 1f);
            hr.sharedMaterial = hm;
            hr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            hr.receiveShadows = false;
        }

        Collider hc = head.GetComponent<Collider>();
        if (hc != null)
            DestroyImmediate(hc);

        return 1;
    }
'''

text = replace_method(text, "private void BuildAnchorL1FromDxf", new_build_anchor)
text = replace_method(text, "private int CreateAnchorPolyline", new_create_anchor)

path.write_text(text, encoding="utf-8")
print("앙카 1차 보정 완료: L1만 생성, L2/L3 중지, 1단 띠장 높이 기준")
