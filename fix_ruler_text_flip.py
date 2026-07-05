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


new_text_method = r'''
    private void CreateElevationRulerText(GameObject parent, string text, Vector3 pos, Vector3 modelCenter, float size, Color color)
    {
        GameObject obj = new GameObject("HEIGHT_TEXT_" + text);
        obj.transform.SetParent(parent.transform, false);
        obj.transform.position = pos;

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = text;
        tm.fontSize = 180;
        tm.characterSize = size * 0.16f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = color;
        tm.richText = false;
        tm.fontStyle = FontStyle.Bold;

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 180);
        if (font != null)
        {
            tm.font = font;
            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.sharedMaterial = font.material;
                mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                mr.receiveShadows = false;
            }
        }

        Vector3 outward = pos - modelCenter;
        outward.y = 0f;

        if (outward.sqrMagnitude < 0.001f)
            outward = Vector3.forward;

        outward.Normalize();

        // 중요:
        // 기존 방향은 바깥쪽에서 볼 때 TextMesh 뒷면이 보여 숫자가 좌우반전될 수 있음.
        // 180도 뒤집어서 기준자 바깥쪽에서 정방향으로 읽히게 한다.
        obj.transform.rotation = Quaternion.LookRotation(outward, Vector3.up) * Quaternion.Euler(0f, 180f, 0f);
    }
'''

text = replace_method(text, "private void CreateElevationRulerText", new_text_method)

path.write_text(text, encoding="utf-8")
print("높이 기준자 숫자 좌우반전 수정 완료")
