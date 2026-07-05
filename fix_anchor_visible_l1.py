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

            float headDist = GetNearestDistanceXZ(anchorHead, pfCenters);

            // 기존 400f가 너무 강해서 전부 제외될 수 있으므로 완화
            // 그래도 너무 먼 도면기호는 제외
            if (headDist > 2500f)
                return 0;
        }

        Vector3 dir = anchorTail - anchorHead;
        dir.y = 0f;

        float originalLen = dir.magnitude;
        if (originalLen < 0.05f)
            return 0;

        dir.Normalize();

        // 화면 검토용: CAD 원본 길이가 짧아도 최소 8m 이상 보이게 강제
        float displayLen = Mathf.Clamp(originalLen, 8.0f, 12.28f);

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

        // 너무 얇으면 안 보이므로 굵게
        anchor.transform.localScale = new Vector3(0.22f, 0.22f, displayLen);
        anchor.transform.rotation = Quaternion.LookRotation(slopedDir, Vector3.up);

        Renderer r = anchor.GetComponent<Renderer>();
        if (r != null)
        {
            Material mat = new Material(Shader.Find("Standard"));
            mat.color = new Color(0.95f, 1.0f, 0.05f, 1f);
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
        head.transform.localScale = Vector3.one * 0.65f;

        Renderer hr = head.GetComponent<Renderer>();
        if (hr != null)
        {
            Material hm = new Material(Shader.Find("Standard"));
            hm.color = new Color(1.0f, 0.05f, 0.02f, 1f);
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

        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        List<Vector3> pfCentersForAnchor = LoadPfCentersForAnchorHead();

        int createdL1 = 0;
        int skipped = 0;

        float anchorY = -1.00f;

        try
        {
            anchorY = -GetWaleSpecDepthByBand(1);
        }
        catch
        {
            anchorY = -1.00f;
        }

        Debug.Log("[ANCHOR] source entity count: " + data.entities.Count);
        Debug.Log("[ANCHOR] pf center count: " + pfCentersForAnchor.Count);
        Debug.Log("[ANCHOR] anchorY: " + anchorY);

        foreach (var e in data.entities)
        {
            int made = CreateAnchorPolyline(group, e, anchorY, "ANCHOR_L1_SPEC", pfCentersForAnchor);
            if (made > 0)
                createdL1 += made;
            else
                skipped++;
        }

        group.SetActive(false);

        Debug.Log("========== ANCHOR 도면기준 1차 보정 ==========");
        Debug.Log("ANCHOR_L1_SPEC 생성: " + createdL1);
        Debug.Log("ANCHOR 제외/스킵: " + skipped);
        Debug.Log("ANCHOR_L1 child count: " + group.transform.childCount);
        Debug.Log("기준: 1단 띠장 높이에 맞춤. 기존 L2/L3 자동 생성 중지.");
        Debug.Log("==============================================");
    }
'''

text = replace_method(text, "private int CreateAnchorPolyline", new_create_anchor)
text = replace_method(text, "private void BuildAnchorL1FromDxf", new_build_anchor)

path.write_text(text, encoding="utf-8")
print("앙카 가시화/스킵 완화 수정 완료")
