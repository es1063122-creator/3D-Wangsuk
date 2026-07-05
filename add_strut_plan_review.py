from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# BuildAll 안에 STRUT 평면 검토 레이어 호출 추가
if 'BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT");' not in text:
    text = text.replace(
'''        BuildWaleLevelsByPfCenters("c605_pf_hpile.json", "WALE");''',
'''        BuildWaleLevelsByPfCenters("c605_pf_hpile.json", "WALE");

        // C-605 평면도 STRUT / BEAM-BRACING 레이어 기준
        // 버팀 평면 위치 검토용. 단수/높이는 C-612~C-619 전개도 확인 후 적용.
        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT");'''
    )

append_func = r'''
    private void BuildStrutPlanFromDxf(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("C605 STRUT PLAN JSON 없음 또는 비어 있음: " + fileName);
            return;
        }

        GameObject group = registry.GetGroup(groupKey);

        if (group == null)
        {
            GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
            if (root == null)
                root = new GameObject("Wangsuk_CAD_3D_ROOT");

            group = new GameObject("STRUT");
            group.transform.SetParent(root.transform, false);

            Debug.LogWarning("STRUT 그룹이 없어 강제 생성했습니다.");
        }

        int strutCreated = 0;
        int beamBracingCreated = 0;

        foreach (var e in data.entities)
        {
            if (!e.has_points || e.points == null || e.points.Count < 2)
                continue;

            string layer = e.layer != null ? e.layer.ToUpper() : "";

            if (layer.Contains("BEAM-BRACING"))
                beamBracingCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "BEAM_BRACING_PLAN", true);
            else
                strutCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "STRUT_PLAN", false);
        }

        Debug.Log("========== C605 STRUT 평면 검토 ==========");
        Debug.Log("STRUT 일반 버팀 생성: " + strutCreated);
        Debug.Log("BEAM-BRACING 코너/대각 후보 생성: " + beamBracingCreated);
        Debug.Log("주의: 현재는 평면 위치 검토용. 단수/높이는 전개도 확인 후 적용.");
        Debug.Log("========================================");
    }

    private int CreateStrutPlanPolyline(GameObject group, WangsukDxfEntity e, float y, string label, bool isBeamBracing)
    {
        List<Vector3> pts = ConvertEntityPoints(e, y);

        int segCount = e.closed && pts.Count > 2 ? pts.Count : pts.Count - 1;
        int created = 0;

        Material mat = new Material(Shader.Find("Standard"));

        if (isBeamBracing)
            mat.color = new Color(1.0f, 0.05f, 0.75f, 1f);   // 코너/대각 후보: 진한 분홍
        else
            mat.color = new Color(0.65f, 0.1f, 1.0f, 1f);     // 일반 버팀: 보라

        for (int i = 0; i < segCount; i++)
        {
            Vector3 a = pts[i];
            Vector3 b = pts[(i + 1) % pts.Count];

            Vector3 dir = b - a;
            float len = dir.magnitude;

            if (len < 0.05f)
                continue;

            GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
            beam.name = "C605_" + label + "_" + created;
            beam.transform.SetParent(group.transform, false);

            beam.transform.position = (a + b) * 0.5f;

            // 검토용이라 우선 눈에 보이게 표현
            float width = isBeamBracing ? 0.90f : 0.65f;
            float height = isBeamBracing ? 0.70f : 0.55f;

            beam.transform.localScale = new Vector3(width, height, len);
            beam.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);
            beam.GetComponent<Renderer>().material = mat;

            created++;
        }

        return created;
    }
'''

if "private void BuildStrutPlanFromDxf" not in text:
    idx = text.rfind("}")
    text = text[:idx] + append_func + "\n}"
    print("STRUT 평면 검토 함수 추가 완료")
else:
    print("STRUT 평면 검토 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
