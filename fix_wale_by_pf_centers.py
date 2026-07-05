from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# BuildAll 안의 호출을 PF 중심점 기반 함수로 교체
text = text.replace(
    'BuildWaleLevelsByPfNo("c605_pf_hpile.json", "WALE");',
    'BuildWaleLevelsByPfCenters("c605_pf_hpile.json", "WALE");'
)

append_func = r'''
    private Vector3 GetEntityCenterPoint(WangsukDxfEntity e, float y)
    {
        Vector3 sum = Vector3.zero;
        int count = 0;

        if (e == null || e.points == null)
            return Vector3.zero;

        foreach (var p in e.points)
        {
            Vector3 v = CadCoordinateSystem.ToUnityPoint(p);
            sum += v;
            count++;
        }

        if (count <= 0)
            return Vector3.zero;

        Vector3 center = sum / count;
        center.y = y;
        return center;
    }

    private void BuildWaleLevelsByPfCenters(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("WALE 중심점 생성 실패: PF JSON 데이터 없음");
            return;
        }

        GameObject group = registry.GetGroup(groupKey);

        if (group == null)
        {
            GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
            if (root == null)
                root = new GameObject("Wangsuk_CAD_3D_ROOT");

            group = new GameObject("WALE");
            group.transform.SetParent(root.transform, false);

            Debug.LogWarning("WALE 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var e in data.entities)
        {
            if (!e.has_points || e.points == null || e.points.Count < 2)
                continue;

            centers.Add(GetEntityCenterPoint(e, 0f));
        }

        int created = 0;

        for (int i = 0; i < centers.Count - 1; i++)
        {
            int pfNo = i + 1;
            int levels = GetWaleLevelByPfNo(pfNo);

            Vector3 a = centers[i];
            Vector3 b = centers[i + 1];

            float dist = Vector3.Distance(a, b);

            // 너무 큰 점프는 DXF 순서가 끊긴 구간일 가능성이 있어 제외
            if (dist > 20f)
                continue;

            if (levels >= 1)
                created += CreateWaleBeamBetweenCenters(group, a, b, waleDepth1, "P" + pfNo.ToString("000") + "_L1_0.6m");

            if (levels >= 2)
                created += CreateWaleBeamBetweenCenters(group, a, b, waleDepth2, "P" + pfNo.ToString("000") + "_L2_3.6m");

            if (levels >= 3)
                created += CreateWaleBeamBetweenCenters(group, a, b, waleDepth3, "P" + pfNo.ToString("000") + "_L3_5.6m");
        }

        Debug.Log("========== WALE 중심점 생성 진단 ==========");
        Debug.Log("PF center count = " + centers.Count);
        Debug.Log("C605 WALE 중심점 기반 생성 = " + created);
        Debug.Log("WALE 기준: P001~P097=2단, P098~P365=3단, P366~P405=2단, P406~P492=3단");
        Debug.Log("========================================");
    }

    private int CreateWaleBeamBetweenCenters(GameObject group, Vector3 a, Vector3 b, float depthMeter, string levelName)
    {
        if (group == null)
            return 0;

        a.y = -depthMeter;
        b.y = -depthMeter;

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.05f)
            return 0;

        Vector3 mid = (a + b) * 0.5f;

        GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
        beam.name = "C605_WALE_CENTER_2H_" + levelName;
        beam.transform.SetParent(group.transform, false);

        beam.transform.position = mid;

        // 2H 띠장처럼 눈에 보이게 두껍게 표현
        beam.transform.localScale = new Vector3(1.05f, 0.55f, len);
        beam.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 0.72f, 0f, 1f);
        beam.GetComponent<Renderer>().material = mat;

        return 1;
    }
'''

if "private void BuildWaleLevelsByPfCenters" not in text:
    idx = text.rfind("}")
    text = text[:idx] + append_func + "\n}"
    print("PF 중심점 기반 WALE 함수 추가 완료")
else:
    print("PF 중심점 기반 WALE 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료:", path)
