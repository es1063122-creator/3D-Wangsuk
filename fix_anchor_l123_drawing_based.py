from pathlib import Path
import re

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


# 기존 C605 앵커 직접 호출을 도면기준 PF/띠장 단수 앵커 호출로 확실히 교체
text = re.sub(
    r'BuildAnchorL1FromDxf\s*\(\s*"c605_anchor_l1\.json"\s*,\s*"ANCHOR_L1"\s*\)\s*;',
    'BuildAnchorSpecReviewFromPfCenters("c605_pf_hpile.json", "ANCHOR_L1");',
    text,
    count=1
)

text = re.sub(
    r'BuildAnchorL1FromDxf\s*\(\s*"c605_anchor_l1\.json"\s*,\s*"ANCHOR_L1"\s*\)\s*\n\s*;',
    'BuildAnchorSpecReviewFromPfCenters("c605_pf_hpile.json", "ANCHOR_L1");',
    text,
    count=1
)


new_anchor_class = r'''
    private class AnchorSpecRange
    {
        public int startNo;
        public int endNo;
        public string source;
        public int level;
        public int step;
        public int skipStart;
        public int skipEnd;
        public bool enabled;

        public AnchorSpecRange(int s, int e, string src, int lv, int interval, int skipS, int skipE, bool use)
        {
            startNo = s;
            endNo = e;
            source = src;
            level = lv;
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

        // 기존 앵커 중복 제거
        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        GameObject l1Group = new GameObject("ANCHOR_L1_LEVEL");
        GameObject l2Group = new GameObject("ANCHOR_L2_LEVEL");
        GameObject l3Group = new GameObject("ANCHOR_L3_LEVEL");

        l1Group.transform.SetParent(group.transform, false);
        l2Group.transform.SetParent(group.transform, false);
        l3Group.transform.SetParent(group.transform, false);

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

        // 띠장 중심 높이 기준. 실패 시 검토용 기본값 적용
        float y1 = -1.00f;
        float y2 = -3.00f;
        float y3 = -5.00f;

        try { y1 = -GetWaleSpecDepthByBand(1); } catch { y1 = -1.00f; }
        try { y2 = -GetWaleSpecDepthByBand(2); } catch { y2 = y1 - 2.00f; }
        try { y3 = -GetWaleSpecDepthByBand(3); } catch { y3 = y2 - 2.00f; }

        // 더 얇고 더 투명하게
        Material anchorMatL1 = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.075f));
        Material anchorMatL2 = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.060f));
        Material anchorMatL3 = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.050f));
        Material headMat = CreateAnchorSpecMaterial(new Color(1.0f, 0.18f, 0.02f, 0.16f));

        // 도면 기준 적용:
        // 전개도 @토목-앵커 레이어 = 설치 구간 확인
        // 단면도 1/2/3단 표기 + 띠장 단수 = 단수/높이 기준
        AnchorSpecRange[] ranges = new AnchorSpecRange[]
        {
            // 1단: 전개도 앵커 구간 전체
            new AnchorSpecRange(1,   67,  "C-612", 1, 5, 2, 2, true),
            new AnchorSpecRange(67,  131, "C-613", 1, 5, 2, 2, true),
            new AnchorSpecRange(131, 196, "C-614", 1, 5, 2, 2, true),
            new AnchorSpecRange(196, 248, "C-615", 1, 5, 2, 2, true),
            new AnchorSpecRange(248, 306, "C-616", 1, 5, 2, 2, true),
            new AnchorSpecRange(306, 365, "C-617", 1, 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 1, 5, 2, 2, true),
            new AnchorSpecRange(428, 492, "C-619", 1, 5, 2, 3, true),

            // 2단: 2단 띠장 존재 구간
            new AnchorSpecRange(1,   67,  "C-612", 2, 5, 2, 2, true),
            new AnchorSpecRange(67,  131, "C-613", 2, 5, 2, 2, true),
            new AnchorSpecRange(131, 196, "C-614", 2, 5, 2, 2, true),
            new AnchorSpecRange(196, 248, "C-615", 2, 5, 2, 2, true),
            new AnchorSpecRange(248, 306, "C-616", 2, 5, 2, 2, true),
            new AnchorSpecRange(306, 365, "C-617", 2, 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 2, 5, 2, 2, true),
            new AnchorSpecRange(428, 492, "C-619", 2, 5, 2, 3, true),

            // 3단: 3단 띠장/단면 확인 구간
            // 일부 구간은 도면검토 기준으로 부분 적용
            new AnchorSpecRange(95,  116, "C-613", 3, 5, 1, 1, true),
            new AnchorSpecRange(178, 196, "C-614", 3, 5, 1, 1, true),
            new AnchorSpecRange(196, 248, "C-615", 3, 5, 2, 2, true),
            new AnchorSpecRange(248, 258, "C-616A", 3, 5, 1, 1, true),
            new AnchorSpecRange(278, 306, "C-616B", 3, 5, 1, 1, true),
            new AnchorSpecRange(306, 365, "C-617", 3, 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 3, 5, 2, 2, true),
            new AnchorSpecRange(428, 469, "C-619", 3, 5, 2, 2, true)
        };

        int createdL1 = 0;
        int createdL2 = 0;
        int createdL3 = 0;

        foreach (var r in ranges)
        {
            if (!r.enabled)
                continue;

            GameObject targetGroup = l1Group;
            float y = y1;
            Material mat = anchorMatL1;

            if (r.level == 2)
            {
                targetGroup = l2Group;
                y = y2;
                mat = anchorMatL2;
            }
            else if (r.level == 3)
            {
                targetGroup = l3Group;
                y = y3;
                mat = anchorMatL3;
            }

            int made = CreateAnchorSpecRange(targetGroup, centers, globalCenter, r, y, mat, headMat);

            if (r.level == 1) createdL1 += made;
            else if (r.level == 2) createdL2 += made;
            else if (r.level == 3) createdL3 += made;
        }

        group.SetActive(false);

        Debug.Log("========== ANCHOR_SPEC_REVIEW 1/2/3단 도면기준 생성 ==========");
        Debug.Log("[ANCHOR_SPEC] PF center count: " + centers.Count);
        Debug.Log("[ANCHOR_SPEC] L1 생성: " + createdL1 + " / y=" + y1);
        Debug.Log("[ANCHOR_SPEC] L2 생성: " + createdL2 + " / y=" + y2);
        Debug.Log("[ANCHOR_SPEC] L3 생성: " + createdL3 + " / y=" + y3);
        Debug.Log("[ANCHOR_SPEC] 기준: 전개도 @토목-앵커 구간 + 단면도 1/2/3단 + 띠장 단수 높이");
        Debug.Log("[ANCHOR_SPEC] 표시: 더 얇게 / 더 투명하게 / 4단은 미생성");
        Debug.Log("=============================================================");
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
            Debug.Log("[ANCHOR_SPEC] " + range.source + " L" + range.level + " 생성 없음: skip 범위 과다");
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

            Vector3 n1 = Vector3.Cross(Vector3.up, tangent).normalized;
            Vector3 n2 = -n1;

            Vector3 radialOut = pf - globalCenter;
            radialOut.y = 0f;

            if (radialOut.sqrMagnitude < 0.0001f)
                radialOut = n1;

            radialOut.Normalize();

            Vector3 outward = Vector3.Dot(n1, radialOut) >= Vector3.Dot(n2, radialOut) ? n1 : n2;
            outward = (outward * 0.78f + radialOut * 0.22f).normalized;

            // 단수가 내려갈수록 머리점이 살짝 더 바깥으로 보이도록 미세 오프셋
            float headOffset = 0.42f + (range.level - 1) * 0.05f;
            Vector3 head = new Vector3(pf.x, anchorY, pf.z) + outward * headOffset;

            float displayLen = 12.28f;
            float downwardAngleDeg = 15.0f;
            float rad = downwardAngleDeg * Mathf.Deg2Rad;

            Vector3 slopedDir = outward * Mathf.Cos(rad) + Vector3.down * Mathf.Sin(rad);
            slopedDir.Normalize();

            Vector3 tail = head + slopedDir * displayLen;

            GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            anchor.name = "ANCHOR_L" + range.level + "_" + range.source + "_P" + no.ToString("000");
            anchor.transform.SetParent(group.transform, false);
            anchor.transform.position = (head + tail) * 0.5f;

            // 더 얇게
            anchor.transform.localScale = new Vector3(0.040f, 0.040f, displayLen);
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
            headSphere.name = "ANCHOR_HEAD_L" + range.level + "_" + range.source + "_P" + no.ToString("000");
            headSphere.transform.SetParent(group.transform, false);
            headSphere.transform.position = head;

            // 머리점도 작게
            headSphere.transform.localScale = Vector3.one * 0.14f;

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

        Debug.Log("[ANCHOR_SPEC] " + range.source + " L" + range.level + " P" + range.startNo.ToString("000") + "~P" + range.endNo.ToString("000") + " / step=" + range.step + " / 생성=" + created);
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

        mat.renderQueue = 3200;
        return mat;
    }
'''


# AnchorSpecRange 클래스 교체
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
    if end < 0:
        raise SystemExit("AnchorSpecRange 클래스 끝을 찾지 못했습니다.")
    text = text[:old_class_start] + new_anchor_class + text[end:]
else:
    marker = "    private void BuildAnchorSpecReviewFromPfCenters"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("AnchorSpecRange 삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + new_anchor_class + "\n" + text[idx:]


text = replace_method(text, "private void BuildAnchorSpecReviewFromPfCenters", new_build)
text = replace_method(text, "private int CreateAnchorSpecRange", new_range)
text = replace_method(text, "private Material CreateAnchorSpecMaterial", new_mat)

path.write_text(text, encoding="utf-8")
print("도면기준 1/2/3단 앵커 생성 + 얇기/투명도 보정 완료")
