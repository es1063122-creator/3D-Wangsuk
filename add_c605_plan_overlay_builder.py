from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# using System.IO 추가
if "using System.IO;" not in text:
    text = text.replace("using System.Collections.Generic;", "using System.Collections.Generic;\nusing System.IO;")
    print("using System.IO 추가 완료")

call = '''        // C-605 굴착계획 평면도 바닥 도면 오버레이
        BuildC605PlanOverlay("c605_pf_hpile.json");'''

if "BuildC605PlanOverlay(" not in text:
    if 'BuildBottomElZones("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildBottomElZones("c605_pf_hpile.json");''',
'''        BuildBottomElZones("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 도면 오버레이 호출 추가 완료")
    elif 'BuildExcavationFaceBottomAndText("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");''',
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 도면 오버레이 호출 추가 완료")
    else:
        print("삽입 기준 호출을 찾지 못했습니다.")
else:
    print("도면 오버레이 호출 이미 있음")

helper = r'''
    private void BuildC605PlanOverlay(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("도면 오버레이용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("PLAN_OVERLAY");
        if (group == null)
        {
            group = new GameObject("PLAN_OVERLAY");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("PLAN_OVERLAY 그룹이 없어 강제 생성했습니다.");
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
            Debug.LogWarning("도면 오버레이 생성 실패: PF center 부족");
            return;
        }

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minZ = float.MaxValue;
        float maxZ = float.MinValue;

        foreach (var p in centers)
        {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.z < minZ) minZ = p.z;
            if (p.z > maxZ) maxZ = p.z;
        }

        float padX = (maxX - minX) * 0.035f;
        float padZ = (maxZ - minZ) * 0.035f;

        minX -= padX;
        maxX += padX;
        minZ -= padZ;
        maxZ += padZ;

        string imgPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Overlay", "c605_plan_overlay.png");

        if (!File.Exists(imgPath))
        {
            Debug.LogWarning("도면 오버레이 PNG 없음: " + imgPath);
            return;
        }

        byte[] bytes = File.ReadAllBytes(imgPath);
        Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        tex.LoadImage(bytes);
        tex.wrapMode = TextureWrapMode.Clamp;
        tex.filterMode = FilterMode.Bilinear;

        Material mat = new Material(Shader.Find("Unlit/Transparent"));
        if (mat.shader == null)
            mat = new Material(Shader.Find("Standard"));

        mat.mainTexture = tex;
        mat.color = new Color(1f, 1f, 1f, 0.68f);
        mat.renderQueue = 2990;

        float y = -7.25f;

        Vector3 v0 = new Vector3(minX, y, minZ);
        Vector3 v1 = new Vector3(maxX, y, minZ);
        Vector3 v2 = new Vector3(maxX, y, maxZ);
        Vector3 v3 = new Vector3(minX, y, maxZ);

        GameObject obj = new GameObject("C605_PLAN_OVERLAY_TEXTURE");
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = new Vector3[] { v0, v1, v2, v3 };
        mesh.triangles = new int[] { 0, 2, 1, 0, 3, 2 };

        // 필요 시 뒤집힘 보정은 여기 UV 순서만 바꾸면 됨
        mesh.uv = new Vector2[]
        {
            new Vector2(0f, 0f),
            new Vector2(1f, 0f),
            new Vector2(1f, 1f),
            new Vector2(0f, 1f)
        };

        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;

        // 기본은 OFF. 필요할 때 도면 버튼으로 켠다.
        group.SetActive(false);

        Debug.Log("========== C605 평면도 도면 오버레이 생성 ==========");
        Debug.Log("PLAN_OVERLAY 생성 완료: " + imgPath);
        Debug.Log("기준: C-605 PF/H-PILE bbox와 동일 정규화 좌표에 투명 PNG 배치.");
        Debug.Log("기본 OFF: 도면 버튼으로 표시");
        Debug.Log("===============================================");
    }
'''

if "private void BuildC605PlanOverlay" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("도면 오버레이 함수 추가 완료")
else:
    print("도면 오버레이 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
