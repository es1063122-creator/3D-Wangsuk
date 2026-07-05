from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 색상 더 선명하게
text = text.replace(
'''Material fillMat = CreateSoilRockMaterial(new Color(0.62f, 0.44f, 0.25f, 1f));       // 매립층
        Material sedimentMat = CreateSoilRockMaterial(new Color(0.74f, 0.61f, 0.40f, 1f));   // 퇴적층
        Material wsMat = CreateSoilRockMaterial(new Color(0.83f, 0.67f, 0.32f, 1f));         // 풍화토
        Material wrMat = CreateSoilRockMaterial(new Color(0.48f, 0.48f, 0.43f, 1f));         // 풍화암''',
'''Material fillMat = CreateSoilRockMaterial(new Color(0.45f, 0.25f, 0.08f, 1f));       // 매립층 - 진갈색
        Material sedimentMat = CreateSoilRockMaterial(new Color(0.78f, 0.55f, 0.22f, 1f));   // 퇴적층 - 황갈색
        Material wsMat = CreateSoilRockMaterial(new Color(0.95f, 0.72f, 0.18f, 1f));         // 풍화토 - 황토색
        Material wrMat = CreateSoilRockMaterial(new Color(0.34f, 0.34f, 0.32f, 1f));         // 풍화암 - 진회색'''
)

start = text.find("    private int CreateSoilBandAlongPf(GameObject group, List<Vector3> centers, float topY, float bottomY, Material mat, string namePrefix)")
if start < 0:
    print("CreateSoilBandAlongPf 함수를 찾지 못했습니다.")
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

    new_func = r'''    private int CreateSoilBandAlongPf(GameObject group, List<Vector3> centers, float topY, float bottomY, Material mat, string namePrefix)
    {
        int created = 0;

        Vector3 globalCenter = Vector3.zero;
        foreach (var c in centers)
            globalCenter += c;
        globalCenter /= centers.Count;

        for (int i = 0; i < centers.Count - 1; i++)
        {
            Vector3 c0 = centers[i];
            Vector3 c1 = centers[i + 1];

            Vector3 aTop = new Vector3(c0.x, topY, c0.z);
            Vector3 bTop = new Vector3(c1.x, topY, c1.z);

            float dist = Vector3.Distance(aTop, bTop);

            // DXF 순서가 크게 튀는 구간은 제외
            if (dist < 0.05f || dist > 20f)
                continue;

            Vector3 segMid = (c0 + c1) * 0.5f;
            Vector3 inward = new Vector3(globalCenter.x - segMid.x, 0f, globalCenter.z - segMid.z);

            if (inward.sqrMagnitude > 0.0001f)
                inward.Normalize();
            else
                inward = Vector3.zero;

            // 기존 굴착면과 z-fighting을 피하기 위해 안쪽으로 살짝 이동
            Vector3 offset = inward * 0.18f;

            aTop += offset;
            bTop += offset;

            Vector3 aBottom = new Vector3(aTop.x, bottomY, aTop.z);
            Vector3 bBottom = new Vector3(bTop.x, bottomY, bTop.z);

            CreateExcavationWallQuad(group, aTop, bTop, bBottom, aBottom, mat, "C605_" + namePrefix + "_" + created);
            created++;
        }

        return created;
    }'''

    text = text[:start] + new_func + text[end:]
    print("CreateSoilBandAlongPf를 offset 방식으로 교체 완료")

path.write_text(text, encoding="utf-8")
print("저장 완료")
