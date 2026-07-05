from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

start = text.find("    private void BuildWaleLevelsByPfNo")
end = text.find("    private int BuildWaleBeamSegments", start)

print("start index =", start)
print("end index   =", end)

new_func = r'''    private void BuildWaleLevelsByPfNo(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("WALE 생성 실패: PF JSON 데이터 없음");
            return;
        }

        GameObject group = registry.GetGroup(groupKey);

        if (group == null)
        {
            GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
            if (root == null)
            {
                root = new GameObject("Wangsuk_CAD_3D_ROOT");
            }

            group = new GameObject("WALE");
            group.transform.SetParent(root.transform, false);

            Debug.LogWarning("WALE 그룹이 Registry에 없어 강제 생성했습니다.");
        }

        int created = 0;
        int pfNo = 1;
        int entityCount = 0;
        int pointEntityCount = 0;

        foreach (var e in data.entities)
        {
            entityCount++;

            if (!e.has_points || e.points == null || e.points.Count < 2)
            {
                pfNo++;
                continue;
            }

            pointEntityCount++;

            int levels = GetWaleLevelByPfNo(pfNo);

            if (levels >= 1)
                created += BuildWaleBeamSegmentsToGroup(group, e, waleDepth1, "P" + pfNo.ToString("000") + "_L1_0.6m");

            if (levels >= 2)
                created += BuildWaleBeamSegmentsToGroup(group, e, waleDepth2, "P" + pfNo.ToString("000") + "_L2_3.6m");

            if (levels >= 3)
                created += BuildWaleBeamSegmentsToGroup(group, e, waleDepth3, "P" + pfNo.ToString("000") + "_L3_5.6m");

            pfNo++;
        }

        Debug.Log("========== WALE 생성 진단 ==========");
        Debug.Log("PF JSON entityCount = " + entityCount);
        Debug.Log("PF points entityCount = " + pointEntityCount);
        Debug.Log("C605 WALE 구간별 단수 생성 = " + created);
        Debug.Log("WALE 기준: P001~P097=2단, P098~P365=3단, P366~P405=2단, P406~P492=3단");
        Debug.Log("==================================");
    }

'''

append_func = r'''
    private int BuildWaleBeamSegmentsToGroup(GameObject group, WangsukDxfEntity e, float depthMeter, string levelName)
    {
        if (group == null)
            return 0;

        List<Vector3> pts = ConvertEntityPoints(e, -depthMeter);

        int segCount = e.closed && pts.Count > 2 ? pts.Count : pts.Count - 1;
        int created = 0;

        for (int i = 0; i < segCount; i++)
        {
            Vector3 a = pts[i];
            Vector3 b = pts[(i + 1) % pts.Count];

            float len = Vector3.Distance(a, b);
            if (len < 0.08f)
                continue;

            Vector3 mid = (a + b) * 0.5f;
            Vector3 dir = (b - a).normalized;

            GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
            beam.name = "C605_WALE_VISIBLE_2H_" + levelName + "_" + created;
            beam.transform.SetParent(group.transform, false);

            beam.transform.position = mid;

            beam.transform.localScale = new Vector3(
                Mathf.Max(waleWidth, 0.85f),
                Mathf.Max(waleHeight, 0.45f),
                len
            );

            beam.transform.rotation = Quaternion.LookRotation(dir, Vector3.up);

            beam.transform.position += beam.transform.right * 0.45f;

            Renderer r = beam.GetComponent<Renderer>();
            if (waleMaterial != null)
            {
                r.material = waleMaterial;
            }
            else
            {
                Material mat = new Material(Shader.Find("Standard"));
                mat.color = new Color(1f, 0.75f, 0f, 1f);
                r.material = mat;
            }

            created++;
        }

        return created;
    }
'''

if start >= 0 and end > start:
    text = text[:start] + new_func + text[end:]
    print("BuildWaleLevelsByPfNo 교체 완료")
else:
    print("BuildWaleLevelsByPfNo 위치를 찾지 못했습니다. 기존 코드는 유지합니다.")

if "BuildWaleBeamSegmentsToGroup" not in text:
    idx = text.rfind("}")
    if idx >= 0:
        text = text[:idx] + append_func + "\n}"
        print("BuildWaleBeamSegmentsToGroup 추가 완료")
    else:
        print("파일 끝 괄호를 찾지 못했습니다.")
else:
    print("BuildWaleBeamSegmentsToGroup 이미 있음")

path.write_text(text, encoding="utf-8")
print("수정 저장 완료:", path)
