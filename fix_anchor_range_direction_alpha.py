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


new_anchor_class = r'''
    private class AnchorSpecRange
    {
        public int startNo;
        public int endNo;
        public string source;
        public int step;
        public int skipStart;
        public int skipEnd;
        public bool enabled;

        public AnchorSpecRange(int s, int e, string src, int interval, int skipS, int skipE, bool use)
        {
            startNo = s;
            endNo = e;
            source = src;
            step = interval;
            skipStart = skipS;
            skipEnd = skipE;
            enabled = use;
        }
    }
'''

new_build = r'''
    private void BuildAnchorSpecReviewFromPfCenters(string pfFileName, string groupKey)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null || pfData.entities.Count == 0)
        {
            Debug.LogError("[ANCHOR_SPEC] PF JSON 없음 또는 비어 있음: " + pfFileName);
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

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("[ANCHOR_SPEC] PF center 부족: " + centers.Count);
            return;
        }

        Vector3 globalCenter = Vector3.zero;
        foreach (var c in centers)
            globalCenter += c;
        globalCenter /= centers.Count;

        float anchorY = -1.00f;
        try
        {
            anchorY = -GetWaleSpecDepthByBand(1);
        }
        catch
        {
            anchorY = -1.00f;
        }

        // 더 투명하게 조정
        Material anchorMat = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.18f));
        Material headMat = CreateAnchorSpecMaterial(new Color(1.0f, 0.18f, 0.02f, 0.38f));

        // step: 앙카 간격
        // skipStart/skipEnd: 구간 경계·코너부 제외 개수
        // enabled=false로 바꾸면 해당 구간 앙카 제외 가능
        AnchorSpecRange[] ranges = new AnchorSpecRange[]
        {
            new AnchorSpecRange(1,   67,  "C-612", 5, 2, 2, true),
            new AnchorSpecRange(67,  131, "C-613", 5, 2, 2, true),
            new AnchorSpecRange(131, 196, "C-614", 5, 2, 2, true),
            new AnchorSpecRange(196, 248, "C-615", 5, 2, 2, true),
            new AnchorSpecRange(248, 306, "C-616", 5, 2, 2, true),
            new AnchorSpecRange(306, 365, "C-617", 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 5, 2, 2, true),
            new AnchorSpecRange(428, 492, "C-619", 5, 2, 3, true)
        };

        int created = 0;

        foreach (var r in ranges)
        {
            if (!r.enabled)
            {
                Debug.Log("[ANCHOR_SPEC] " + r.source + " 제외 처리");
                continue;
            }

            created += CreateAnchorSpecRange(group, centers, globalCenter, r, anchorY, anchorMat, headMat);
        }

        group.SetActive(false);

        Debug.Log("========== ANCHOR_SPEC_REVIEW 정밀 보정 ==========");
        Debug.Log("[ANCHOR_SPEC] PF center count: " + centers.Count);
        Debug.Log("[ANCHOR_SPEC] 생성 앵커 수: " + created);
        Debug.Log("[ANCHOR_SPEC] 기준: 구간별 step/코너부 제외/local wall normal 방향/1단 띠장 중심/반투명");
        Debug.Log("=================================================");
    }
'''

new_range = r'''
    private int CreateAnchorSpecRange(
        GameObject group,
        List<Vector3> centers,
        Vector3 globalCenter,
        AnchorSpecRange range,
        float anchorY,
        Material anchorMat,
        Material headMat)
    {
        int created = 0;

        int start = Mathf.Clamp(range.startNo + range.skipStart, 1, centers.Count);
        int end = Mathf.Clamp(range.endNo - range.skipEnd, 1, centers.Count);

        if (end < start)
        {
            Debug.Log("[ANCHOR_SPEC] " + range.source + " 생성 없음: skip 범위 과다");
            return 0;
        }

        int step = Mathf.Max(1, range.step);

        for (int no = start; no <= end; no += step)
        {
            int idx = no - 1;
            if (idx < 0 || idx >= centers.Count)
                continue;

            Vector3 pf = centers[idx];

            int prevIdx = (idx - 1 + centers.Count) % centers.Count;
            int nextIdx = (idx + 1) % centers.Count;

            Vector3 prev = centers[prevIdx];
            Vector3 next = centers[nextIdx];

            Vector3 tangent = next - prev;
            tangent.y = 0f;

            if (tangent.sqrMagnitude < 0.0001f)
                continue;

            tangent.Normalize();

            // local wall normal 후보 2개 중, global center에서 멀어지는 방향을 outward로 선택
            Vector3 n1 = Vector3.Cross(Vector3.up, tangent).normalized;
            Vector3 n2 = -n1;

            Vector3 radialOut = pf - globalCenter;
            radialOut.y = 0f;

            if (radialOut.sqrMagnitude < 0.0001f)
                radialOut = n1;

            radialOut.Normalize();

            Vector3 outward = Vector3.Dot(n1, radialOut) >= Vector3.Dot(n2, radialOut) ? n1 : n2;

            // 코너부 방향 안정화: radial과 local normal을 섞어서 급격한 꺾임 완화
            outward = (outward * 0.78f + radialOut * 0.22f).normalized;

            // 머리점은 1단 띠장 중심 근처.
            // 너무 바깥이면 0.35 낮추고, 너무 안쪽이면 0.75로 올리면 됨.
            float headOffset = 0.52f;
            Vector3 head = new Vector3(pf.x, anchorY, pf.z) + outward * headOffset;

            float displayLen = 12.28f;
            float downwardAngleDeg = 15.0f;
            float rad = downwardAngleDeg * Mathf.Deg2Rad;

            Vector3 slopedDir = outward * Mathf.Cos(rad) + Vector3.down * Mathf.Sin(rad);
            slopedDir.Normalize();

            Vector3 tail = head + slopedDir * displayLen;

            GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            anchor.name = "ANCHOR_SPEC_" + range.source + "_P" + no.ToString("000");
            anchor.transform.SetParent(group.transform, false);
            anchor.transform.position = (head + tail) * 0.5f;
            anchor.transform.localScale = new Vector3(0.11f, 0.11f, displayLen);
            anchor.transform.rotation = Quaternion.LookRotation(slopedDir, Vector3.up);

            Renderer ar = anchor.GetComponent<Renderer>();
            if (ar != null)
            {
                ar.sharedMaterial = anchorMat;
                ar.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                ar.receiveShadows = false;
            }

            Collider ac = anchor.GetComponent<Collider>();
            if (ac != null)
                DestroyImmediate(ac);

            GameObject headSphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            headSphere.name = "ANCHOR_HEAD_" + range.source + "_P" + no.ToString("000");
            headSphere.transform.SetParent(group.transform, false);
            headSphere.transform.position = head;
            headSphere.transform.localScale = Vector3.one * 0.34f;

            Renderer hr = headSphere.GetComponent<Renderer>();
            if (hr != null)
            {
                hr.sharedMaterial = headMat;
                hr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                hr.receiveShadows = false;
            }

            Collider hc = headSphere.GetComponent<Collider>();
            if (hc != null)
                DestroyImmediate(hc);

            created++;
        }

        Debug.Log("[ANCHOR_SPEC] " + range.source + " P" + range.startNo.ToString("000") + "~P" + range.endNo.ToString("000") + " / step=" + range.step + " / skip=" + range.skipStart + "," + range.skipEnd + " / 생성=" + created);
        return created;
    }
'''

new_mat = r'''
    private Material CreateAnchorSpecMaterial(Color color)
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

        mat.renderQueue = 3150;
        return mat;
    }
'''

# class 교체
old_class_start = text.find("    private class AnchorSpecRange")
if old_class_start >= 0:
    brace = text.find("{", old_class_start)
    depth = 0
    end = -1
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    text = text[:old_class_start] + new_anchor_class + text[end:]

text = replace_method(text, "private void BuildAnchorSpecReviewFromPfCenters", new_build)
text = replace_method(text, "private int CreateAnchorSpecRange", new_range)
text = replace_method(text, "private Material CreateAnchorSpecMaterial", new_mat)

path.write_text(text, encoding="utf-8")
print("앙카 구간별 간격/코너 방향/머리점/투명도 정밀 보정 완료")
