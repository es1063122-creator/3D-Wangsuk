from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // C-605 PF/H-PILE 중심선 기준 굴착면/바닥/바닥 글씨 생성
        // 실제 토질/암질 층 및 정확한 EL은 굴착계획 전개도/단면도 검토 후 추가 보정
        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");'''

if "BuildExcavationFaceBottomAndText(" not in text:
    if 'BuildAnchorL1FromDxf("c605_anchor_l1.json", "ANCHOR_L1");' in text:
        text = text.replace(
'''        BuildAnchorL1FromDxf("c605_anchor_l1.json", "ANCHOR_L1");''',
'''        BuildAnchorL1FromDxf("c605_anchor_l1.json", "ANCHOR_L1");

''' + call
        )
        print("BuildAll에 굴착면/바닥/글씨 생성 호출 추가 완료")
    elif 'BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");' in text:
        text = text.replace(
'''        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");''',
'''        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");

''' + call
        )
        print("BuildAll에 굴착면/바닥/글씨 생성 호출 추가 완료")
    else:
        print("호출 삽입 기준 문구를 찾지 못했습니다.")
else:
    print("굴착면/바닥/글씨 생성 호출 이미 있음")

helper = r'''
    private void BuildExcavationFaceBottomAndText(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("굴착면 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject faceGroup = registry.GetGroup("EXCAVATION_FACE");
        if (faceGroup == null)
        {
            faceGroup = new GameObject("EXCAVATION_FACE");
            faceGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("EXCAVATION_FACE 그룹이 없어 강제 생성했습니다.");
        }

        GameObject bottomGroup = registry.GetGroup("EXCAVATION_BOTTOM");
        if (bottomGroup == null)
        {
            bottomGroup = new GameObject("EXCAVATION_BOTTOM");
            bottomGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("EXCAVATION_BOTTOM 그룹이 없어 강제 생성했습니다.");
        }

        GameObject textGroup = registry.GetGroup("BOTTOM_EL_TEXT");
        if (textGroup == null)
        {
            textGroup = new GameObject("BOTTOM_EL_TEXT");
            textGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("BOTTOM_EL_TEXT 그룹이 없어 강제 생성했습니다.");
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

        if (centers.Count < 3)
        {
            Debug.LogWarning("굴착면 생성 실패: PF center 부족");
            return;
        }

        // 현재 1차 기준값.
        // 도면 전개도/단면도에서 구간별 시공하한선 EL 확정 후 bottomY는 구간별로 보정 예정.
        float groundY = 0.0f;
        float bottomY = -8.0f;

        Material faceMat = new Material(Shader.Find("Standard"));
        faceMat.color = new Color(0.48f, 0.36f, 0.22f, 0.92f);

        Material bottomMat = new Material(Shader.Find("Standard"));
        bottomMat.color = new Color(0.58f, 0.52f, 0.43f, 1f);

        int faceCreated = 0;

        for (int i = 0; i < centers.Count - 1; i++)
        {
            Vector3 aTop = new Vector3(centers[i].x, groundY, centers[i].z);
            Vector3 bTop = new Vector3(centers[i + 1].x, groundY, centers[i + 1].z);

            float dist = Vector3.Distance(aTop, bTop);

            // DXF 순서가 크게 튀는 구간은 제외
            if (dist < 0.05f || dist > 20f)
                continue;

            Vector3 aBottom = new Vector3(aTop.x, bottomY, aTop.z);
            Vector3 bBottom = new Vector3(bTop.x, bottomY, bTop.z);

            CreateExcavationWallQuad(faceGroup, aTop, bTop, bBottom, aBottom, faceMat, "C605_EXCAVATION_FACE_" + faceCreated);
            faceCreated++;
        }

        int bottomCreated = CreateExcavationBottomMesh(bottomGroup, centers, bottomY, bottomMat);

        Vector3 center = Vector3.zero;
        foreach (var p in centers)
            center += p;
        center /= centers.Count;

        CreateBlackWorldText(textGroup, "굴착저면\nEL 검토", new Vector3(center.x, bottomY + 0.08f, center.z), 1.25f);

        Debug.Log("========== C605 굴착면/바닥 생성 ==========");
        Debug.Log("EXCAVATION_FACE 벽면 생성: " + faceCreated);
        Debug.Log("EXCAVATION_BOTTOM 바닥 생성: " + bottomCreated);
        Debug.Log("BOTTOM_EL_TEXT 검정 글씨 생성: 1");
        Debug.Log("현재 기준: PF/H-PILE 중심선 기반, groundY=0, bottomY=-8.0. 실제 EL/토질/암질은 다음 단계에서 도면 기준 보정.");
        Debug.Log("==========================================");
    }

    private void CreateExcavationWallQuad(GameObject group, Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, Material mat, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = new Vector3[]
        {
            p0, p1, p2, p3
        };

        mesh.triangles = new int[]
        {
            0, 1, 2,
            0, 2, 3
        };

        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;
    }

    private int CreateExcavationBottomMesh(GameObject group, List<Vector3> centers, float bottomY, Material mat)
    {
        if (centers == null || centers.Count < 3)
            return 0;

        List<Vector3> clean = new List<Vector3>();

        for (int i = 0; i < centers.Count; i++)
        {
            if (i > 0)
            {
                float d = Vector3.Distance(centers[i], centers[i - 1]);
                if (d > 20f)
                    continue;
            }

            clean.Add(new Vector3(centers[i].x, bottomY, centers[i].z));
        }

        if (clean.Count < 3)
            return 0;

        Vector3 center = Vector3.zero;
        foreach (var p in clean)
            center += p;
        center /= clean.Count;

        List<Vector3> vertices = new List<Vector3>();
        vertices.Add(center);
        vertices.AddRange(clean);

        List<int> tris = new List<int>();

        for (int i = 1; i < vertices.Count - 1; i++)
        {
            tris.Add(0);
            tris.Add(i);
            tris.Add(i + 1);
        }

        // 마지막 폐합
        tris.Add(0);
        tris.Add(vertices.Count - 1);
        tris.Add(1);

        GameObject obj = new GameObject("C605_EXCAVATION_BOTTOM_SURFACE");
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = vertices.ToArray();
        mesh.triangles = tris.ToArray();
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;

        return 1;
    }

    private void CreateBlackWorldText(GameObject group, string text, Vector3 position, float size)
    {
        GameObject obj = new GameObject("C605_BOTTOM_EL_TEXT");
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = position;

        // 바닥면 위에 눕혀서 보이게 배치
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = text;
        tm.fontSize = 80;
        tm.characterSize = size * 0.08f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        MeshRenderer mr = obj.GetComponent<MeshRenderer>();
        if (mr != null)
        {
            Material mat = new Material(Shader.Find("Standard"));
            mat.color = Color.black;
            mr.material = mat;
        }
    }
'''

if "private void BuildExcavationFaceBottomAndText" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("굴착면/바닥/검정글씨 함수 추가 완료")
else:
    print("굴착면/바닥/검정글씨 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
