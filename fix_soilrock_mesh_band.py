from pathlib import Path

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


new_method = r'''
    private int CreateSoilBandAlongPf(GameObject group, List<Vector3> centers, float topY, float bottomY, Material mat, string namePrefix)
    {
        if (group == null || centers == null || centers.Count < 2)
            return 0;

        Vector3 globalCenter = Vector3.zero;
        foreach (var c in centers)
            globalCenter += c;
        globalCenter /= centers.Count;

        float yTop = Mathf.Max(topY, bottomY);
        float yBottom = Mathf.Min(topY, bottomY);

        // 캡빔 안쪽에 자연스럽게 붙는 폭/위치
        float insideOffset = 0.75f;
        float bandWidth = 1.85f;

        List<Vector3> verts = new List<Vector3>();
        List<int> tris = new List<int>();

        int segmentCount = 0;

        for (int i = 0; i < centers.Count; i++)
        {
            Vector3 a = centers[i];
            Vector3 b = centers[(i + 1) % centers.Count];

            Vector3 dir = b - a;
            dir.y = 0f;

            float len = dir.magnitude;

            // 비정상 연결 제외
            if (len < 0.05f)
                continue;

            if (len > 12.0f)
                continue;

            dir.Normalize();

            Vector3 mid = (a + b) * 0.5f;
            Vector3 inward = globalCenter - mid;
            inward.y = 0f;

            if (inward.sqrMagnitude < 0.0001f)
                inward = Vector3.Cross(Vector3.up, dir);

            inward.Normalize();

            Vector3 aOuter = a + inward * insideOffset;
            Vector3 bOuter = b + inward * insideOffset;
            Vector3 aInner = a + inward * (insideOffset + bandWidth);
            Vector3 bInner = b + inward * (insideOffset + bandWidth);

            aOuter.y = yTop;
            bOuter.y = yTop;
            aInner.y = yTop;
            bInner.y = yTop;

            Vector3 aOuterBot = new Vector3(aOuter.x, yBottom, aOuter.z);
            Vector3 bOuterBot = new Vector3(bOuter.x, yBottom, bOuter.z);
            Vector3 aInnerBot = new Vector3(aInner.x, yBottom, aInner.z);
            Vector3 bInnerBot = new Vector3(bInner.x, yBottom, bInner.z);

            int v = verts.Count;

            // 0 top outer A
            // 1 top outer B
            // 2 top inner B
            // 3 top inner A
            // 4 bottom outer A
            // 5 bottom outer B
            // 6 bottom inner B
            // 7 bottom inner A
            verts.Add(aOuter);
            verts.Add(bOuter);
            verts.Add(bInner);
            verts.Add(aInner);
            verts.Add(aOuterBot);
            verts.Add(bOuterBot);
            verts.Add(bInnerBot);
            verts.Add(aInnerBot);

            // 상부면
            tris.Add(v + 0); tris.Add(v + 1); tris.Add(v + 2);
            tris.Add(v + 0); tris.Add(v + 2); tris.Add(v + 3);

            // 하부면
            tris.Add(v + 4); tris.Add(v + 6); tris.Add(v + 5);
            tris.Add(v + 4); tris.Add(v + 7); tris.Add(v + 6);

            // 외측 수직면
            tris.Add(v + 0); tris.Add(v + 4); tris.Add(v + 5);
            tris.Add(v + 0); tris.Add(v + 5); tris.Add(v + 1);

            // 내측 수직면
            tris.Add(v + 3); tris.Add(v + 2); tris.Add(v + 6);
            tris.Add(v + 3); tris.Add(v + 6); tris.Add(v + 7);

            // 시작 단면
            tris.Add(v + 0); tris.Add(v + 3); tris.Add(v + 7);
            tris.Add(v + 0); tris.Add(v + 7); tris.Add(v + 4);

            // 끝 단면
            tris.Add(v + 1); tris.Add(v + 5); tris.Add(v + 6);
            tris.Add(v + 1); tris.Add(v + 6); tris.Add(v + 2);

            segmentCount++;
        }

        if (verts.Count == 0)
            return 0;

        GameObject go = new GameObject(namePrefix + "_MESH_BAND");
        go.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.name = namePrefix + "_Mesh";
        mesh.SetVertices(verts);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = go.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = go.AddComponent<MeshRenderer>();
        mr.sharedMaterial = mat;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        mr.receiveShadows = false;

        Debug.Log("[SOIL_ROCK_LAYER] " + namePrefix + " 연속 Mesh 지층밴드 생성: " + segmentCount);

        return segmentCount;
    }
'''

text = replace_method(text, "private int CreateSoilBandAlongPf", new_method)

path.write_text(text, encoding="utf-8")
print("CreateSoilBandAlongPf 연속 Mesh 지층밴드 방식으로 수정 완료")
