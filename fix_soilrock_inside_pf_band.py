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

        int created = 0;

        Vector3 globalCenter = Vector3.zero;
        foreach (var c in centers)
            globalCenter += c;
        globalCenter /= centers.Count;

        float height = Mathf.Abs(topY - bottomY);
        float centerY = (topY + bottomY) * 0.5f;

        // 캡빔/포스트파일 안쪽으로 들어오는 폭
        // 값이 크면 내부로 두껍게 들어오고, 작으면 벽에 붙음
        float bandWidth = 2.40f;

        // 포스트파일 중심선에서 안쪽으로 이동하는 거리
        // 캡빔과 겹치지 않게 살짝 안쪽에 배치
        float insideOffset = 1.55f;

        for (int i = 0; i < centers.Count; i++)
        {
            Vector3 a = centers[i];
            Vector3 b = centers[(i + 1) % centers.Count];

            Vector3 dir = b - a;
            dir.y = 0f;

            float len = dir.magnitude;

            // 너무 짧거나 비정상적으로 긴 연결은 제외
            if (len < 0.05f)
                continue;

            if (len > 12.0f)
                continue;

            dir.Normalize();

            Vector3 mid = (a + b) * 0.5f;
            mid.y = centerY;

            Vector3 inward = globalCenter - mid;
            inward.y = 0f;

            if (inward.sqrMagnitude < 0.0001f)
                inward = Vector3.Cross(Vector3.up, dir);

            inward.Normalize();

            // PF 중심선보다 내부로 이동
            Vector3 pos = mid + inward * insideOffset;
            pos.y = centerY;

            GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = namePrefix + "_INSIDE_" + i.ToString("000");
            go.transform.SetParent(group.transform, false);

            go.transform.position = pos;

            // local z축을 PF 진행방향에 맞춤
            go.transform.rotation = Quaternion.LookRotation(dir, Vector3.up);

            // x = 내부 폭, y = 층 높이, z = PF 구간 길이
            go.transform.localScale = new Vector3(bandWidth, height, len * 1.04f);

            Renderer r = go.GetComponent<Renderer>();
            if (r != null)
            {
                r.sharedMaterial = mat;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                r.receiveShadows = false;
            }

            Collider c = go.GetComponent<Collider>();
            if (c != null)
                DestroyImmediate(c);

            created++;
        }

        Debug.Log("[SOIL_ROCK_LAYER] " + namePrefix + " 내부 지층밴드 생성: " + created);
        return created;
    }
'''

text = replace_method(text, "private int CreateSoilBandAlongPf", new_method)

path.write_text(text, encoding="utf-8")
print("CreateSoilBandAlongPf를 캡빔 안쪽 PF라인 지층밴드 방식으로 수정 완료")
