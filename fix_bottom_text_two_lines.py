from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 호출 문구를 두 줄용 기준 텍스트로 정리
text = text.replace('"BOTTOM EL\\nCHECK"', '"BOTTOM EL|CHECK"')
text = text.replace('"BOTTOM EL\nCHECK"', '"BOTTOM EL|CHECK"')
text = text.replace('"굴착저면\\nEL 검토"', '"BOTTOM EL|CHECK"')

start = text.find("    private void CreateBlackWorldText(GameObject group, string text, Vector3 position, float size)")
if start < 0:
    print("CreateBlackWorldText 함수를 찾지 못했습니다.")
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

    new_func = r'''    private void CreateBlackWorldText(GameObject group, string text, Vector3 position, float size)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_BOTTOM_EL_TEXT_WHITE_PLATE";
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.02f, position.z);
        plate.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
        plate.transform.localScale = new Vector3(8.5f, 0.025f, 3.2f);

        Material plateMat = new Material(Shader.Find("Standard"));
        plateMat.color = Color.white;
        plate.GetComponent<Renderer>().material = plateMat;

        string line1 = "BOTTOM EL";
        string line2 = "CHECK";

        if (!string.IsNullOrEmpty(text))
        {
            string[] parts = text.Split('|');
            if (parts.Length >= 2)
            {
                line1 = parts[0];
                line2 = parts[1];
            }
        }

        Font arial = Font.CreateDynamicFontFromOSFont("Arial", 96);

        CreateFlatBlackTextLine(group, line1, new Vector3(position.x, position.y + 0.10f, position.z + 0.45f), size, arial, "C605_BOTTOM_EL_TEXT_LINE_1");
        CreateFlatBlackTextLine(group, line2, new Vector3(position.x, position.y + 0.10f, position.z - 0.45f), size, arial, "C605_BOTTOM_EL_TEXT_LINE_2");
    }

    private void CreateFlatBlackTextLine(GameObject group, string label, Vector3 position, float size, Font font, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = position;

        // 바닥 위에 눕혀서 위에서 읽히도록 배치
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.095f;
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
    }'''

    text = text[:start] + new_func + text[end:]
    print("CreateBlackWorldText를 2개 TextMesh 방식으로 교체 완료")

path.write_text(text, encoding="utf-8")
print("저장 완료")
