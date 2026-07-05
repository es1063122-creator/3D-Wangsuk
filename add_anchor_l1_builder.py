from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# BuildAll에 앵커 생성 호출 추가
if 'BuildAnchorL1FromDxf("c605_anchor_l1.json", "ANCHOR_L1");' not in text:
    text = text.replace(
'''        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");''',
'''        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");

        // C-605 평면도 Anchor_1단 / ANCHOR 레이어 기준
        // 길이 1000 이상 본체만 ANCHOR_L1로 생성
        BuildAnchorL1FromDxf("c605_anchor_l1.json", "ANCHOR_L1");'''
    )
    print("BuildAll에 ANCHOR_L1 생성 호출 추가")
else:
    print("ANCHOR_L1 호출 이미 있음")

helper = r'''
    private void BuildAnchorL1FromDxf(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("C605 ANCHOR_L1 JSON 없음 또는 비어 있음: " + fileName);
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

        int created = 0;
        foreach (var e in data.entities)
        {
            created += CreateAnchorPolyline(group, e, -waleDepth1, "ANCHOR_L1");
        }

        Debug.Log("========== C605 ANCHOR 생성 ==========");
        Debug.Log("ANCHOR_L1 본체 생성: " + created);
        Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상만 사용.");
        Debug.Log("====================================");
    }

    private int CreateAnchorPolyline(GameObject group, WangsukDxfEntity e, float y, string label)
    {
        List<Vector3> pts = ConvertEntityPoints(e, y);
        if (pts == null || pts.Count < 2)
            return 0;

        Vector3 a = pts[0];
        Vector3 b = pts[pts.Count - 1];

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.10f)
            return 0;

        GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        anchor.name = "C605_" + label;

        anchor.transform.SetParent(group.transform, false);
        anchor.transform.position = (a + b) * 0.5f;

        // 앵커는 길고 얇게 표현
        anchor.transform.localScale = new Vector3(0.10f, 0.10f, len);
        anchor.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0.75f, 1.0f, 0.10f, 1f); // 연두/노랑
        anchor.GetComponent<Renderer>().material = mat;

        return 1;
    }
'''

if "private void BuildAnchorL1FromDxf" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("ANCHOR_L1 생성 함수 추가")
else:
    print("ANCHOR_L1 생성 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
