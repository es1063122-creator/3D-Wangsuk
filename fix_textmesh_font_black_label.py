from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 한글 문구가 남아 있으면 영어로 교체
text = text.replace('굴착저면\\nEL 검토', 'BOTTOM EL\\nCHECK')
text = text.replace('"굴착저면\\nEL 검토"', '"BOTTOM EL\\nCHECK"')

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
        // 검정 글씨가 어두운 바닥에 묻히지 않도록 얇은 흰색 받침판을 먼저 만든다.
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_BOTTOM_EL_TEXT_WHITE_PLATE";
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.02f, position.z);
        plate.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
        plate.transform.localScale = new Vector3(7.0f, 0.025f, 2.4f);

        Material plateMat = new Material(Shader.Find("Standard"));
        plateMat.color = Color.white;
        plate.GetComponent<Renderer>().material = plateMat;

        GameObject obj = new GameObject("C605_BOTTOM_EL_TEXT");
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = new Vector3(position.x, position.y + 0.08f, position.z);

        // 바닥 위에 눕혀서 위에서 읽히도록 배치
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = text;
        tm.fontSize = 96;
        tm.characterSize = size * 0.09f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        // TextMesh에는 Standard 머티리얼을 쓰면 글자가 깨져 보일 수 있음.
        // Arial 동적 폰트 + 폰트 전용 머티리얼 사용.
        Font arial = Font.CreateDynamicFontFromOSFont("Arial", 96);
        if (arial != null)
        {
            tm.font = arial;

            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = arial.material;
                mr.material.color = Color.black;
            }
        }
    }'''

    text = text[:start] + new_func + text[end:]
    print("CreateBlackWorldText 함수 교체 완료")

path.write_text(text, encoding="utf-8")
print("저장 완료")
