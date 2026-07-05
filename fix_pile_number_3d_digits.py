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
        root.transform.position = worldPos + new Vector3(0f, 0.25f, 0f);

        Material digitMat = CreatePostPileNumberDigitMaterial();

        // 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "원형외곽_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = Vector3.zero;
        outline.transform.localRotation = Quaternion.identity;
        outline.transform.localScale = new Vector3(1.15f, 0.04f, 1.15f);

        Renderer outlineRenderer = outline.GetComponent<Renderer>();
        if (outlineRenderer != null)
        {
            outlineRenderer.sharedMaterial = outlineMat;
            outlineRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            outlineRenderer.receiveShadows = false;
        }

        Collider outlineCol = outline.GetComponent<Collider>();
        if (outlineCol != null) DestroyImmediate(outlineCol);

        // 내부 원
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "원형번호판_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = new Vector3(0f, 0.055f, 0f);
        disc.transform.localRotation = Quaternion.identity;
        disc.transform.localScale = new Vector3(0.92f, 0.035f, 0.92f);

        Renderer discRenderer = disc.GetComponent<Renderer>();
        if (discRenderer != null)
        {
            discRenderer.sharedMaterial = discMat;
            discRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            discRenderer.receiveShadows = false;
        }

        Collider discCol = disc.GetComponent<Collider>();
        if (discCol != null) DestroyImmediate(discCol);

        // 숫자를 TextMesh가 아니라 검은색 3D 막대 숫자로 생성
        CreatePileNumberDigits3D(root.transform, no.ToString(), digitMat);
    }
'''

helpers = r'''

    private Material CreatePostPileNumberDigitMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 4100;
        return mat;
    }

    private void CreatePileNumberDigits3D(Transform parent, string numberText, Material mat)
    {
        int len = numberText.Length;

        float digitWidth = 0.30f;
        float digitHeight = 0.50f;
        float gap = 0.08f;

        float totalWidth = len * digitWidth + (len - 1) * gap;
        float startX = -totalWidth * 0.5f + digitWidth * 0.5f;

        for (int i = 0; i < len; i++)
        {
            char ch = numberText[i];
            float x = startX + i * (digitWidth + gap);
            CreateSevenSegmentDigit(parent, ch, new Vector3(x, 0.145f, 0f), digitWidth, digitHeight, mat);
        }
    }

    private void CreateSevenSegmentDigit(Transform parent, char ch, Vector3 center, float width, float height, Material mat)
    {
        // 7세그먼트 위치
        //   A
        // F   B
        //   G
        // E   C
        //   D

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

        float t = 0.055f;
        float y = center.y;
        float zTop = center.z + height * 0.42f;
        float zMid = center.z;
        float zBot = center.z - height * 0.42f;
        float xLeft = center.x - width * 0.42f;
        float xRight = center.x + width * 0.42f;

        float hLen = width * 0.72f;
        float vLen = height * 0.36f;

        if (A) CreateDigitBar(parent, "A", new Vector3(center.x, y, zTop), new Vector3(hLen, t, t), mat);
        if (G) CreateDigitBar(parent, "G", new Vector3(center.x, y, zMid), new Vector3(hLen, t, t), mat);
        if (D) CreateDigitBar(parent, "D", new Vector3(center.x, y, zBot), new Vector3(hLen, t, t), mat);

        if (B) CreateDigitBar(parent, "B", new Vector3(xRight, y, center.z + height * 0.21f), new Vector3(t, t, vLen), mat);
        if (C) CreateDigitBar(parent, "C", new Vector3(xRight, y, center.z - height * 0.21f), new Vector3(t, t, vLen), mat);
        if (F) CreateDigitBar(parent, "F", new Vector3(xLeft, y, center.z + height * 0.21f), new Vector3(t, t, vLen), mat);
        if (E) CreateDigitBar(parent, "E", new Vector3(xLeft, y, center.z - height * 0.21f), new Vector3(t, t, vLen), mat);
    }

    private void CreateDigitBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
        bar.name = "DIGIT_BAR_" + name;
        bar.transform.SetParent(parent, false);
        bar.transform.localPosition = localPos;
        bar.transform.localScale = localScale;

        Renderer r = bar.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider col = bar.GetComponent<Collider>();
        if (col != null) DestroyImmediate(col);
    }

'''

text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

if "private void CreatePileNumberDigits3D" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreatePostPileNumberDiscMaterial 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("PILE번호 숫자를 3D 막대 숫자 방식으로 수정 완료")
