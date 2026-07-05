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


new_marker = r'''
    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);

        // 캡빔 상단보다 확실히 위에 올림
        root.transform.position = worldPos + new Vector3(0f, 6.0f, 0f);
        root.transform.rotation = Quaternion.identity;

        Material plateMat = CreatePostPileNumberDiscMaterial();
        Material borderMat = CreatePostPileNumberOutlineMaterial();
        Material digitMat = CreatePostPileNumberDigitMaterial();

        // 큰 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "번호원외곽_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = Vector3.zero;
        outline.transform.localScale = new Vector3(1.75f, 0.08f, 1.75f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = borderMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 큰 흰색 번호판
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "번호원판_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = new Vector3(0f, 0.09f, 0f);
        disc.transform.localScale = new Vector3(1.48f, 0.08f, 1.48f);

        Renderer dr = disc.GetComponent<Renderer>();
        if (dr != null)
        {
            dr.sharedMaterial = plateMat;
            dr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            dr.receiveShadows = false;
        }

        Collider dc = disc.GetComponent<Collider>();
        if (dc != null) DestroyImmediate(dc);

        // 검은색 3D 숫자
        CreatePileNumberDigitsBig3D(root.transform, no.ToString(), digitMat);
    }
'''

helpers = r'''

    private void CreatePileNumberDigitsBig3D(Transform parent, string numberText, Material mat)
    {
        int len = numberText.Length;

        float digitWidth = 0.36f;
        float digitHeight = 0.70f;
        float gap = 0.08f;

        if (len == 1)
        {
            digitWidth = 0.46f;
            digitHeight = 0.82f;
        }
        else if (len == 2)
        {
            digitWidth = 0.40f;
            digitHeight = 0.76f;
        }

        float totalWidth = len * digitWidth + (len - 1) * gap;
        float startX = -totalWidth * 0.5f + digitWidth * 0.5f;

        for (int i = 0; i < len; i++)
        {
            char ch = numberText[i];
            float x = startX + i * (digitWidth + gap);
            CreateSevenSegmentDigitBig(parent, ch, new Vector3(x, 0.28f, 0f), digitWidth, digitHeight, mat);
        }
    }

    private void CreateSevenSegmentDigitBig(Transform parent, char ch, Vector3 center, float width, float height, Material mat)
    {
        bool A = false, B = false, C = false, D = false, E = false, F = false, G = false;

        switch (ch)
        {
            case '0': A = B = C = D = E = F = true; break;
            case '1': B = C = true; break;
            case '2': A = B = G = E = D = true; break;
            case '3': A = B = C = D = G = true; break;
            case '4': F = G = B = C = true; break;
            case '5': A = F = G = C = D = true; break;
            case '6': A = F = E = D = C = G = true; break;
            case '7': A = B = C = true; break;
            case '8': A = B = C = D = E = F = G = true; break;
            case '9': A = B = C = D = F = G = true; break;
            default: return;
        }

        float t = 0.09f;
        float y = center.y;

        float zTop = center.z + height * 0.42f;
        float zMid = center.z;
        float zBot = center.z - height * 0.42f;

        float xLeft = center.x - width * 0.43f;
        float xRight = center.x + width * 0.43f;

        float hLen = width * 0.76f;
        float vLen = height * 0.38f;

        if (A) CreatePileDigitCube(parent, "A", new Vector3(center.x, y, zTop), new Vector3(hLen, 0.12f, t), mat);
        if (G) CreatePileDigitCube(parent, "G", new Vector3(center.x, y, zMid), new Vector3(hLen, 0.12f, t), mat);
        if (D) CreatePileDigitCube(parent, "D", new Vector3(center.x, y, zBot), new Vector3(hLen, 0.12f, t), mat);

        if (B) CreatePileDigitCube(parent, "B", new Vector3(xRight, y, center.z + height * 0.21f), new Vector3(t, 0.12f, vLen), mat);
        if (C) CreatePileDigitCube(parent, "C", new Vector3(xRight, y, center.z - height * 0.21f), new Vector3(t, 0.12f, vLen), mat);
        if (F) CreatePileDigitCube(parent, "F", new Vector3(xLeft, y, center.z + height * 0.21f), new Vector3(t, 0.12f, vLen), mat);
        if (E) CreatePileDigitCube(parent, "E", new Vector3(xLeft, y, center.z - height * 0.21f), new Vector3(t, 0.12f, vLen), mat);
    }

    private void CreatePileDigitCube(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "PILE_DIGIT_" + name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localScale = localScale;

        Renderer r = go.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = go.GetComponent<Collider>();
        if (c != null) DestroyImmediate(c);
    }

'''

text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

if "private void CreatePileNumberDigitsBig3D" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreatePostPileNumberDiscMaterial 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

# 재료 색상 강제 보정
def replace_mat(src, signature, body):
    try:
        return replace_method(src, signature, body)
    except SystemExit:
        return src

text = replace_mat(text, "private Material CreatePostPileNumberDiscMaterial()", r'''
    private Material CreatePostPileNumberDiscMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 1f, 1f);
        mat.renderQueue = 3500;
        return mat;
    }
''')

text = replace_mat(text, "private Material CreatePostPileNumberOutlineMaterial()", r'''
    private Material CreatePostPileNumberOutlineMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 3490;
        return mat;
    }
''')

text = replace_mat(text, "private Material CreatePostPileNumberDigitMaterial()", r'''
    private Material CreatePostPileNumberDigitMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 5000;
        return mat;
    }
''')

path.write_text(text, encoding="utf-8")
print("PILE번호를 큰 원형판 + 큰 3D 숫자로 수정 완료")
