from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 기존 CreateSoilRockMaterial 함수를 반투명 재질 함수로 교체
start = text.find("    private Material CreateSoilRockMaterial(Color color)")
if start < 0:
    print("CreateSoilRockMaterial 함수를 찾지 못했습니다.")
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

    new_func = r'''    private Material CreateSoilRockMaterial(Color color)
    {
        // 지층/암질 색띠 전용 반투명 재질
        Shader shader = Shader.Find("Standard");
        Material mat = new Material(shader);

        mat.color = color;

        // Built-in Standard Shader 투명 설정
        mat.SetFloat("_Mode", 3f); // Transparent
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;

        return mat;
    }'''

    text = text[:start] + new_func + text[end:]
    print("CreateSoilRockMaterial 반투명 재질 방식으로 교체 완료")

# 지층 색상 알파값 적용
old_colors = '''Material fillMat = CreateSoilRockMaterial(new Color(0.45f, 0.25f, 0.08f, 1f));       // 매립층 - 진갈색
        Material sedimentMat = CreateSoilRockMaterial(new Color(0.78f, 0.55f, 0.22f, 1f));   // 퇴적층 - 황갈색
        Material wsMat = CreateSoilRockMaterial(new Color(0.95f, 0.72f, 0.18f, 1f));         // 풍화토 - 황토색
        Material wrMat = CreateSoilRockMaterial(new Color(0.34f, 0.34f, 0.32f, 1f));         // 풍화암 - 진회색'''

new_colors = '''Material fillMat = CreateSoilRockMaterial(new Color(0.45f, 0.25f, 0.08f, 0.35f));       // 매립층 - 반투명 진갈색
        Material sedimentMat = CreateSoilRockMaterial(new Color(0.78f, 0.55f, 0.22f, 0.35f));   // 퇴적층 - 반투명 황갈색
        Material wsMat = CreateSoilRockMaterial(new Color(0.95f, 0.72f, 0.18f, 0.40f));         // 풍화토 - 반투명 황토색
        Material wrMat = CreateSoilRockMaterial(new Color(0.34f, 0.34f, 0.32f, 0.45f));         // 풍화암 - 반투명 진회색'''

if old_colors in text:
    text = text.replace(old_colors, new_colors)
    print("지층 색상 알파값 적용 완료")
else:
    print("기존 색상 블록을 찾지 못했습니다. 개별 치환 시도")

    text = text.replace(
        "CreateSoilRockMaterial(new Color(0.45f, 0.25f, 0.08f, 1f))",
        "CreateSoilRockMaterial(new Color(0.45f, 0.25f, 0.08f, 0.35f))"
    )
    text = text.replace(
        "CreateSoilRockMaterial(new Color(0.78f, 0.55f, 0.22f, 1f))",
        "CreateSoilRockMaterial(new Color(0.78f, 0.55f, 0.22f, 0.35f))"
    )
    text = text.replace(
        "CreateSoilRockMaterial(new Color(0.95f, 0.72f, 0.18f, 1f))",
        "CreateSoilRockMaterial(new Color(0.95f, 0.72f, 0.18f, 0.40f))"
    )
    text = text.replace(
        "CreateSoilRockMaterial(new Color(0.34f, 0.34f, 0.32f, 1f))",
        "CreateSoilRockMaterial(new Color(0.34f, 0.34f, 0.32f, 0.45f))"
    )

path.write_text(text, encoding="utf-8")
print("저장 완료")
