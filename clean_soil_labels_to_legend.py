from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) BOTTOM EL CHECK 생성 호출 완전 제거
text = re.sub(
    r'\s*CreateBlackWorldText\(textGroup,\s*"[^"]*(BOTTOM EL|굴착저면)[^"]*",\s*new Vector3\([^;]+?\);\s*',
    '\n        // 중앙 BOTTOM EL CHECK 테스트 글씨 제거\n',
    text
)

# 2) 지층 글씨 중앙 생성 호출 제거
patterns = [
    r'\s*CreateKoreanFloorLabel\(textGroup,\s*"매립층"[^;]+?\);\s*',
    r'\s*CreateKoreanFloorLabel\(textGroup,\s*"퇴적층"[^;]+?\);\s*',
    r'\s*CreateKoreanFloorLabel\(textGroup,\s*"풍화토"[^;]+?\);\s*',
    r'\s*CreateKoreanFloorLabel\(textGroup,\s*"풍화암"[^;]+?\);\s*',
    r'\s*CreateKoreanFloorLabel\(textGroup,\s*"굴착저면\s+EL\(\+29\.54~31\.00\)"[^;]+?\);\s*',
]

removed = 0
for p in patterns:
    text, n = re.subn(p, '\n        // 중앙 지층 글씨 제거\n', text)
    removed += n

# 3) BuildSoilRockBandsAndLabels 내부에 범례판 생성 호출 추가
target = '''        Debug.Log("========== C605 지층/암질 색띠 생성 ==========");'''

insert = '''        CreateSoilRockLegendBoard(textGroup, centers, bottomY);

'''

if "CreateSoilRockLegendBoard(textGroup, centers, bottomY);" not in text and target in text:
    text = text.replace(target, insert + target)
    print("지층 범례판 생성 호출 추가 완료")
else:
    print("지층 범례판 호출 이미 있음 또는 기준 문구 없음")

# 4) 범례판 함수 추가
helper = r'''
    private void CreateSoilRockLegendBoard(GameObject group, List<Vector3> centers, float bottomY)
    {
        if (centers == null || centers.Count == 0)
            return;

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

        // 모델 내부 중앙이 아니라, 굴착장 외곽 한쪽에 범례를 배치
        Vector3 basePos = new Vector3(minX + 6.0f, bottomY + 0.65f, minZ - 5.5f);

        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "C605_SOIL_ROCK_LEGEND_BOARD";
        board.transform.SetParent(group.transform, false);
        board.transform.position = new Vector3(basePos.x + 4.5f, basePos.y - 0.04f, basePos.z);
        board.transform.localScale = new Vector3(10.5f, 0.035f, 4.8f);

        Material boardMat = new Material(Shader.Find("Standard"));
        boardMat.color = new Color(1f, 1f, 1f, 0.92f);
        board.GetComponent<Renderer>().material = boardMat;

        Font font = Font.CreateDynamicFontFromOSFont("Malgun Gothic", 96);
        if (font == null)
            font = Font.CreateDynamicFontFromOSFont("Arial", 96);

        CreateLegendTextLine(group, "지층 범례", new Vector3(basePos.x + 4.5f, basePos.y + 0.10f, basePos.z + 1.75f), 1.0f, font, "C605_LEGEND_TITLE");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.08f, basePos.z + 0.95f), new Color(0.45f, 0.25f, 0.08f, 0.85f), "BOX_매립층");
        CreateLegendTextLine(group, "매립층", new Vector3(basePos.x + 3.0f, basePos.y + 0.10f, basePos.z + 0.95f), 0.82f, font, "TXT_매립층");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.25f, basePos.z + 0.25f), new Color(0.78f, 0.55f, 0.22f, 0.85f), "BOX_퇴적층");
        CreateLegendTextLine(group, "퇴적층", new Vector3(basePos.x + 3.0f, basePos.y + 0.27f, basePos.z + 0.25f), 0.82f, font, "TXT_퇴적층");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.42f, basePos.z - 0.45f), new Color(0.95f, 0.72f, 0.18f, 0.90f), "BOX_풍화토");
        CreateLegendTextLine(group, "풍화토", new Vector3(basePos.x + 3.0f, basePos.y + 0.44f, basePos.z - 0.45f), 0.82f, font, "TXT_풍화토");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.59f, basePos.z - 1.15f), new Color(0.34f, 0.34f, 0.32f, 0.95f), "BOX_풍화암");
        CreateLegendTextLine(group, "풍화암", new Vector3(basePos.x + 3.0f, basePos.y + 0.61f, basePos.z - 1.15f), 0.82f, font, "TXT_풍화암");

        CreateLegendTextLine(group, "굴착저면  EL(+29.54~31.00)", new Vector3(basePos.x + 5.2f, basePos.y + 0.78f, basePos.z - 2.0f), 0.68f, font, "TXT_굴착저면EL");
    }

    private void CreateLegendColorBox(GameObject group, Vector3 position, Color color, string name)
    {
        GameObject box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = "C605_LEGEND_" + name;
        box.transform.SetParent(group.transform, false);
        box.transform.position = position;
        box.transform.localScale = new Vector3(1.1f, 0.05f, 0.38f);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;
        box.GetComponent<Renderer>().material = mat;
    }

    private void CreateLegendTextLine(GameObject group, string label, Vector3 position, float size, Font font, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = position;
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.08f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = font.material;
                mr.material.color = Color.black;
            }
        }
    }
'''

if "private void CreateSoilRockLegendBoard" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("지층 범례판 함수 추가 완료")
else:
    print("지층 범례판 함수 이미 있음")

path.write_text(text, encoding="utf-8")

print("중앙 지층 글씨 제거 수 =", removed)
print("저장 완료")
