from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

start = text.find("    private int CreateExcavationBottomMesh(GameObject group, List<Vector3> centers, float bottomY, Material mat)")
if start < 0:
    print("CreateExcavationBottomMesh 함수를 찾지 못했습니다.")
else:
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

    new_func = r'''    private int CreateExcavationBottomMesh(GameObject group, List<Vector3> centers, float bottomY, Material mat)
    {
        if (centers == null || centers.Count < 3)
            return 0;

        List<Vector3> hull = BuildConvexHullXZ(centers, bottomY);

        if (hull == null || hull.Count < 3)
        {
            Debug.LogWarning("굴착 바닥 Convex Hull 생성 실패");
            return 0;
        }

        Vector3 center = Vector3.zero;
        foreach (var p in hull)
            center += p;
        center /= hull.Count;

        List<Vector3> vertices = new List<Vector3>();
        vertices.Add(center);
        vertices.AddRange(hull);

        List<int> tris = new List<int>();

        for (int i = 1; i < vertices.Count; i++)
        {
            int next = i + 1;
            if (next >= vertices.Count)
                next = 1;

            tris.Add(0);
            tris.Add(i);
            tris.Add(next);
        }

        GameObject obj = new GameObject("C605_EXCAVATION_BOTTOM_SURFACE_HULL");
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
    }'''

    text = text[:start] + new_func + text[end:]
    print("CreateExcavationBottomMesh를 Convex Hull 방식으로 교체 완료")

helper = r'''
    private List<Vector3> BuildConvexHullXZ(List<Vector3> points, float y)
    {
        List<Vector3> pts = new List<Vector3>();

        foreach (var p in points)
            pts.Add(new Vector3(p.x, y, p.z));

        pts.Sort((a, b) =>
        {
            int cx = a.x.CompareTo(b.x);
            if (cx != 0)
                return cx;
            return a.z.CompareTo(b.z);
        });

        List<Vector3> unique = new List<Vector3>();
        Vector3? last = null;

        foreach (var p in pts)
        {
            if (last == null || Vector3.Distance(p, last.Value) > 0.001f)
            {
                unique.Add(p);
                last = p;
            }
        }

        if (unique.Count < 3)
            return unique;

        List<Vector3> lower = new List<Vector3>();
        foreach (var p in unique)
        {
            while (lower.Count >= 2 && CrossXZ(lower[lower.Count - 2], lower[lower.Count - 1], p) <= 0f)
                lower.RemoveAt(lower.Count - 1);

            lower.Add(p);
        }

        List<Vector3> upper = new List<Vector3>();
        for (int i = unique.Count - 1; i >= 0; i--)
        {
            Vector3 p = unique[i];

            while (upper.Count >= 2 && CrossXZ(upper[upper.Count - 2], upper[upper.Count - 1], p) <= 0f)
                upper.RemoveAt(upper.Count - 1);

            upper.Add(p);
        }

        lower.RemoveAt(lower.Count - 1);
        upper.RemoveAt(upper.Count - 1);

        lower.AddRange(upper);

        return lower;
    }

    private float CrossXZ(Vector3 o, Vector3 a, Vector3 b)
    {
        return (a.x - o.x) * (b.z - o.z) - (a.z - o.z) * (b.x - o.x);
    }
'''

if "private List<Vector3> BuildConvexHullXZ" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("Convex Hull helper 추가 완료")
else:
    print("Convex Hull helper 이미 있음")

# 글씨가 바닥에 묻히지 않도록 조금 더 띄움
text = text.replace(
'''CreateBlackWorldText(textGroup, "굴착저면\\nEL 검토", new Vector3(center.x, bottomY + 0.08f, center.z), 1.25f);''',
'''CreateBlackWorldText(textGroup, "굴착저면\\nEL 검토", new Vector3(center.x, bottomY + 0.35f, center.z), 1.45f);'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
