from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // C-612~C-619 시공하한선 EL 기준 바닥 구역 색상 표시
        BuildBottomElZones("c605_pf_hpile.json");'''

if "BuildBottomElZones(" not in text:
    if 'BuildBottomZoneLines("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildBottomZoneLines("c605_pf_hpile.json");''',
'''        BuildBottomZoneLines("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 바닥 EL 구역 호출 추가 완료")
    elif 'BuildSectionBottomElLabels("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildSectionBottomElLabels("c605_pf_hpile.json");''',
'''        BuildSectionBottomElLabels("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 바닥 EL 구역 호출 추가 완료")
    else:
        print("삽입 기준 호출을 찾지 못했습니다.")
else:
    print("바닥 EL 구역 호출 이미 있음")

helper = r'''
    private void BuildBottomElZones(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("바닥 EL 구역 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("BOTTOM_EL_ZONE");
        if (group == null)
        {
            group = new GameObject("BOTTOM_EL_ZONE");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("BOTTOM_EL_ZONE 그룹이 없어 강제 생성했습니다.");
        }

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
            Debug.LogWarning("바닥 EL 구역 생성 실패: PF center 부족");
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        float y = -7.36f;
        float zoneWidth = 5.8f;

        Material el3044 = CreateBottomElZoneMaterial(new Color(0.45f, 0.70f, 0.95f, 0.38f)); // EL 30.44
        Material el3100 = CreateBottomElZoneMaterial(new Color(0.45f, 0.85f, 0.60f, 0.35f)); // EL 31.00
        Material el2954 = CreateBottomElZoneMaterial(new Color(0.25f, 0.42f, 0.75f, 0.45f)); // EL 29.54
        Material bedrock = CreateBottomElZoneMaterial(new Color(0.25f, 0.25f, 0.25f, 0.50f)); // 기반암층 상단
        Material mixed = CreateBottomElZoneMaterial(new Color(0.80f, 0.80f, 0.80f, 0.30f));   // 복합구간

        // 도면 기준:
        // C-612 P001~067 = EL(+30.44)
        // C-613 P067~131 = EL(+30.44) / EL(+31.00)
        // C-614 P131~196 = EL(+31.00)
        // C-615 P196~248 = EL(+31.00)
        // C-616 P248~306 = EL(+31.00) / EL(+29.54)
        // C-617 P306~365 = EL(+31.00) / EL(+29.54) / 기반암층 상단
        // C-618 P365~428 = EL(+31.00) / EL(+29.54)
        // C-619 P428~492 = EL(+31.00) / EL(+29.54)
        int c1 = CreateBottomElZoneByPfRange(group, centers, allCenter, 1, 67, y, zoneWidth, el3044, "EL3044");
        int c2 = CreateBottomElZoneByPfRange(group, centers, allCenter, 67, 131, y, zoneWidth, mixed, "EL3044_3100");
        int c3 = CreateBottomElZoneByPfRange(group, centers, allCenter, 131, 248, y, zoneWidth, el3100, "EL3100");
        int c4 = CreateBottomElZoneByPfRange(group, centers, allCenter, 248, 306, y, zoneWidth, mixed, "EL3100_2954");
        int c5 = CreateBottomElZoneByPfRange(group, centers, allCenter, 306, 365, y, zoneWidth, bedrock, "BEDROCK_TOP");
        int c6 = CreateBottomElZoneByPfRange(group, centers, allCenter, 365, 492, y, zoneWidth, el2954, "EL2954");

        Debug.Log("========== C605 바닥 EL 구역 색상 생성 ==========");
        Debug.Log("EL(+30.44) 구역 생성: " + c1);
        Debug.Log("EL(+30.44/31.00) 복합 구역 생성: " + c2);
        Debug.Log("EL(+31.00) 구역 생성: " + c3);
        Debug.Log("EL(+31.00/29.54) 복합 구역 생성: " + c4);
        Debug.Log("기반암층 상단 구역 생성: " + c5);
        Debug.Log("EL(+29.54) 구역 생성: " + c6);
        Debug.Log("도면 기준: C-612~C-619 PILE NO 범위와 시공하한선 EL 반영.");
        Debug.Log("==============================================");
    }

    private Material CreateBottomElZoneMaterial(Color color)
    {
        Shader shader = Shader.Find("Standard");
        Material mat = new Material(shader);

        mat.color = color;
        mat.SetFloat("_Mode", 3f);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;

        return mat;
    }

    private int CreateBottomElZoneByPfRange(GameObject group, List<Vector3> centers, Vector3 allCenter, int startPf, int endPf, float y, float width, Material mat, string label)
    {
        if (centers == null || centers.Count < 2)
            return 0;

        int startIndex = Mathf.Clamp(startPf - 1, 0, centers.Count - 1);
        int endIndex = Mathf.Clamp(endPf - 1, 0, centers.Count - 1);

        int created = 0;

        for (int i = startIndex; i < endIndex && i < centers.Count - 1; i++)
        {
            Vector3 c0 = centers[i];
            Vector3 c1 = centers[i + 1];

            float d = Vector3.Distance(c0, c1);
            if (d < 0.05f || d > 20f)
                continue;

            Vector3 mid = (c0 + c1) * 0.5f;
            Vector3 inward = new Vector3(allCenter.x - mid.x, 0f, allCenter.z - mid.z);
            if (inward.sqrMagnitude > 0.0001f)
                inward.Normalize();
            else
                inward = Vector3.zero;

            Vector3 p0 = new Vector3(c0.x, y, c0.z) + inward * 0.65f;
            Vector3 p1 = new Vector3(c1.x, y, c1.z) + inward * 0.65f;
            Vector3 p2 = new Vector3(c1.x, y, c1.z) + inward * width;
            Vector3 p3 = new Vector3(c0.x, y, c0.z) + inward * width;

            GameObject obj = new GameObject("C605_BOTTOM_EL_ZONE_" + label + "_" + created);
            obj.transform.SetParent(group.transform, false);

            Mesh mesh = new Mesh();
            mesh.vertices = new Vector3[] { p0, p1, p2, p3 };
            mesh.triangles = new int[] { 0, 1, 2, 0, 2, 3 };
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();

            MeshFilter mf = obj.AddComponent<MeshFilter>();
            mf.sharedMesh = mesh;

            MeshRenderer mr = obj.AddComponent<MeshRenderer>();
            mr.material = mat;

            created++;
        }

        return created;
    }
'''

if "private void BuildBottomElZones" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("바닥 EL 구역 함수 추가 완료")
else:
    print("바닥 EL 구역 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
