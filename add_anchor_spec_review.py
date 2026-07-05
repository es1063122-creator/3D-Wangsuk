from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

method = r'''

    private class AnchorSpecRange
    {
        public int startNo;
        public int endNo;
        public string source;

        public AnchorSpecRange(int s, int e, string src)
        {
            startNo = s;
            endNo = e;
            source = src;
        }
    }

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

        Material anchorMat = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 1f));
        Material headMat = CreateAnchorSpecMaterial(new Color(1.0f, 0.05f, 0.02f, 1f));

        AnchorSpecRange[] ranges = new AnchorSpecRange[]
        {
            new AnchorSpecRange(1, 67, "C-612"),
            new AnchorSpecRange(67, 131, "C-613"),
            new AnchorSpecRange(131, 196, "C-614"),
            new AnchorSpecRange(196, 248, "C-615"),
            new AnchorSpecRange(248, 306, "C-616"),
            new AnchorSpecRange(306, 365, "C-617"),
            new AnchorSpecRange(365, 428, "C-618"),
            new AnchorSpecRange(428, 492, "C-619")
        };

        int created = 0;

        foreach (var r in ranges)
        {
            created += CreateAnchorSpecRange(group, centers, globalCenter, r, anchorY, anchorMat, headMat);
        }

        group.SetActive(false);

        Debug.Log("========== ANCHOR_SPEC_REVIEW 생성 ==========");
        Debug.Log("[ANCHOR_SPEC] PF center count: " + centers.Count);
        Debug.Log("[ANCHOR_SPEC] 생성 앵커 수: " + created);
        Debug.Log("[ANCHOR_SPEC] 기준: C-612~C-619 PF 번호 구간 / 1단 띠장 높이 / PF 4개 간격");
        Debug.Log("============================================");
    }

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

        int start = Mathf.Clamp(range.startNo, 1, centers.Count);
        int end = Mathf.Clamp(range.endNo, 1, centers.Count);

        if (end < start)
            return 0;

        int step = 4;

        for (int no = start; no <= end; no += step)
        {
            int idx = no - 1;
            if (idx < 0 || idx >= centers.Count)
                continue;

            Vector3 pf = centers[idx];

            Vector3 inward = globalCenter - pf;
            inward.y = 0f;

            if (inward.sqrMagnitude < 0.0001f)
                continue;

            inward.Normalize();

            // 앵커는 굴착장 안쪽이 아니라 배면 지반 방향으로 나가야 하므로 outward 사용
            Vector3 outward = -inward;

            // 머리점은 PF/CIP 바로 바깥쪽, 띠장 접점 근처
            Vector3 head = new Vector3(pf.x, anchorY, pf.z) + outward * 0.75f;

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
            anchor.transform.localScale = new Vector3(0.18f, 0.18f, displayLen);
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
            headSphere.transform.localScale = Vector3.one * 0.55f;

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

        Debug.Log("[ANCHOR_SPEC] " + range.source + " P" + range.startNo.ToString("000") + "~P" + range.endNo.ToString("000") + " 생성: " + created);
        return created;
    }

    private Material CreateAnchorSpecMaterial(Color color)
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;
        return mat;
    }

'''

if "BuildAnchorSpecReviewFromPfCenters" not in text:
    marker = "    private void BuildAnchorL1FromDxf"
    idx = text.find(marker)

    if idx < 0:
        raise SystemExit("BuildAnchorL1FromDxf 위치를 찾지 못했습니다.")

    text = text[:idx] + method + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("PF번호 구간 기준 ANCHOR_SPEC_REVIEW 함수 추가 완료")
