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
    private Material CreateAnchorSpecMaterial(Color color)
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;

        // 반투명 앙카 재질
        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);

        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");

        mat.renderQueue = 3150;
        return mat;
    }
'''

text = replace_method(text, "private Material CreateAnchorSpecMaterial", new_method)

# 앙카 본체 색상: 불투명 노랑 -> 반투명 연노랑
text = text.replace(
'CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 1f))',
'CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.34f))'
)

# 앙카 머리점 색상: 불투명 빨강 -> 반투명 주황빨강
text = text.replace(
'CreateAnchorSpecMaterial(new Color(1.0f, 0.05f, 0.02f, 1f))',
'CreateAnchorSpecMaterial(new Color(1.0f, 0.18f, 0.02f, 0.62f))'
)

path.write_text(text, encoding="utf-8")
print("앙카 반투명 재질 적용 완료")
