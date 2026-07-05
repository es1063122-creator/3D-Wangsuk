from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# BuildAnchorL1FromDxf 안에 PF center 로드 추가
old = '''        int created = 0;
        foreach (var e in data.entities)
        {
            created += CreateAnchorPolyline(group, e, -waleDepth1, "ANCHOR_L1");
        }'''

new = '''        List<Vector3> pfCentersForAnchor = LoadPfCentersForAnchorHead();

        int created = 0;
        foreach (var e in data.entities)
        {
            created += CreateAnchorPolyline(group, e, -waleDepth1, "ANCHOR_L1", pfCentersForAnchor);
        }'''

if old in text:
    text = text.replace(old, new)
    print("앵커 생성부에 PF 기준 머리점 매칭 추가 완료")
else:
    print("앵커 생성부 기준 문구를 찾지 못했습니다. 이미 수정됐거나 구조가 다릅니다.")

# 기존 CreateAnchorPolyline 함수를 새 함수로 교체
start = text.find("    private int CreateAnchorPolyline(GameObject group, WangsukDxfEntity e, float y, string label)")
if start >= 0:
    brace = text.find("{", start)
    depth = 0
    end = brace
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    new_func = r'''    private int CreateAnchorPolyline(GameObject group, WangsukDxfEntity e, float y, string label, List<Vector3> pfCenters)
    {
        List<Vector3> pts = ConvertEntityPoints(e, y);
        if (pts == null || pts.Count < 2)
            return 0;

        Vector3 p0 = pts[0];
        Vector3 p1 = pts[pts.Count - 1];

        Vector3 anchorHead = p0;
        Vector3 anchorTail = p1;

        // PF/CIP 벽체에 더 가까운 끝점을 앵커 머리점으로 사용
        if (pfCenters != null && pfCenters.Count > 0)
        {
            float p0Dist = GetNearestDistanceXZ(p0, pfCenters);
            float p1Dist = GetNearestDistanceXZ(p1, pfCenters);

            if (p1Dist < p0Dist)
            {
                anchorHead = p1;
                anchorTail = p0;
            }
        }

        Vector3 dir = anchorTail - anchorHead;
        float originalLen = dir.magnitude;

        if (originalLen < 0.10f)
            return 0;

        dir.Normalize();

        // 실제 앵커는 너무 길어서 3D 검토 화면을 망가뜨리므로 표시 길이를 제한한다.
        // CAD 원본 길이는 JSON에 보존되어 있고, Unity에서는 벽체 외측 방향 표시용으로 짧게 표현.
        float displayLen = Mathf.Min(originalLen, 4.0f);

        Vector3 a = anchorHead;
        Vector3 b = anchorHead + dir * displayLen;

        GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        anchor.name = "C605_" + label;

        anchor.transform.SetParent(group.transform, false);
        anchor.transform.position = (a + b) * 0.5f;

        anchor.transform.localScale = new Vector3(0.08f, 0.08f, displayLen);
        anchor.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0.75f, 1.0f, 0.10f, 1f);
        anchor.GetComponent<Renderer>().material = mat;

        return 1;
    }'''

    text = text[:start] + new_func + text[end:]
    print("CreateAnchorPolyline 표시 길이 제한 방식으로 교체 완료")
else:
    print("CreateAnchorPolyline 함수를 찾지 못했습니다.")

# helper 추가
helper = r'''
    private List<Vector3> LoadPfCentersForAnchorHead()
    {
        List<Vector3> centers = new List<Vector3>();

        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup("c605_pf_hpile.json");
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogWarning("ANCHOR 머리점 매칭용 PF JSON 없음");
            return centers;
        }

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, -waleDepth1);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        Debug.Log("ANCHOR 머리점 매칭용 PF center count = " + centers.Count);
        return centers;
    }

    private float GetNearestDistanceXZ(Vector3 p, List<Vector3> centers)
    {
        float best = float.MaxValue;

        foreach (var c in centers)
        {
            float dx = p.x - c.x;
            float dz = p.z - c.z;
            float d = dx * dx + dz * dz;

            if (d < best)
                best = d;
        }

        return best;
    }
'''

if "private List<Vector3> LoadPfCentersForAnchorHead()" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("앵커 머리점 매칭 helper 추가 완료")
else:
    print("앵커 helper 이미 있음")

# 로그 문구 보강
text = text.replace(
'''Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상만 사용.");''',
'''Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상만 사용. 화면표시는 벽체 기준 4m로 축소.");'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
