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

        // 캡빔 상단 위에 확실히 띄움
        root.transform.position = worldPos + new Vector3(0f, 4.0f, 0f);
        root.transform.rotation = Quaternion.identity;

        Material plateMat = CreatePostPileNumberBoardMaterial();
        Material borderMat = CreatePostPileNumberOutlineMaterial();
        Material digitMat = CreatePostPileNumberDigitMaterial();

        // 캡빔 상단에 눕는 노란 번호판
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "상단번호판_" + no.ToString("000");
        plate.transform.SetParent(root.transform, false);
        plate.transform.localPosition = Vector3.zero;
        plate.transform.localScale = new Vector3(1.25f, 0.08f, 0.85f);

        Renderer pr = plate.GetComponent<Renderer>();
        if (pr != null)
        {
            pr.sharedMaterial = plateMat;
            pr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            pr.receiveShadows = false;
        }

        Collider pc = plate.GetComponent<Collider>();
        if (pc != null) DestroyImmediate(pc);

        // 번호판 테두리도 눕힘
        CreateFlatNumberPlateBorder(root.transform, borderMat);

        // 검은색 3D 막대 숫자: 폰트 사용 안 함
        CreatePileNumberDigitsFlat3D(root.transform, no.ToString(), digitMat);
    }
'''

helpers = r'''

    private void CreateFlatNumberPlateBorder(Transform parent, Material mat)
    {
        float w = 1.34f;
        float h = 0.94f;
        float t = 0.055f;
        float y = 0.075f;

        CreateFlatDigitBar(parent, "번호판_TOP", new Vector3(0f, y, h * 0.5f), new Vector3(w, 0.06f, t), mat);
        CreateFlatDigitBar(parent, "번호판_BOTTOM", new Vector3(0f, y, -h * 0.5f), new Vector3(w, 0.06f, t), mat);
        CreateFlatDigitBar(parent, "번호판_LEFT", new Vector3(-w * 0.5f, y, 0f), new Vector3(t, 0.06f, h), mat);
        CreateFlatDigitBar(parent, "번호판_RIGHT", new Vector3(w * 0.5f, y, 0f), new Vector3(t, 0.06f, h), mat);
    }

    private Material CreatePostPileNumberDigitMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 5000;
        return mat;
    }

    private void CreatePileNumberDigitsFlat3D(Transform parent, string numberText, Material mat)
    {
        int len = numberText.Length;

        float digitWidth = 0.28f;
        float digitHeight = 0.52f;
        float gap = 0.07f;

        float totalWidth = len * digitWidth + (len - 1) * gap;
        float startX = -totalWidth * 0.5f + digitWidth * 0.5f;

        for (int i = 0; i < len; i++)
        {
            char ch = numberText[i];
            float x = startX + i * (digitWidth + gap);
            CreateSevenSegmentDigitFlat(parent, ch, new Vector3(x, 0.18f, 0f), digitWidth, digitHeight, mat);
        }
    }

    private void CreateSevenSegmentDigitFlat(Transform parent, char ch, Vector3 center, float width, float height, Material mat)
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

        float t = 0.055f;
        float y = center.y;

        float zTop = center.z + height * 0.42f;
        float zMid = center.z;
        float zBot = center.z - height * 0.42f;

        float xLeft = center.x - width * 0.42f;
        float xRight = center.x + width * 0.42f;

        float hLen = width * 0.72f;
        float vLen = height * 0.36f;

        if (A) CreateFlatDigitBar(parent, "DIGIT_A", new Vector3(center.x, y, zTop), new Vector3(hLen, 0.075f, t), mat);
        if (G) CreateFlatDigitBar(parent, "DIGIT_G", new Vector3(center.x, y, zMid), new Vector3(hLen, 0.075f, t), mat);
        if (D) CreateFlatDigitBar(parent, "DIGIT_D", new Vector3(center.x, y, zBot), new Vector3(hLen, 0.075f, t), mat);

        if (B) CreateFlatDigitBar(parent, "DIGIT_B", new Vector3(xRight, y, center.z + height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
        if (C) CreateFlatDigitBar(parent, "DIGIT_C", new Vector3(xRight, y, center.z - height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
        if (F) CreateFlatDigitBar(parent, "DIGIT_F", new Vector3(xLeft, y, center.z + height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
        if (E) CreateFlatDigitBar(parent, "DIGIT_E", new Vector3(xLeft, y, center.z - height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
    }

    private void CreateFlatDigitBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
        bar.name = name;
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

        Collider c = bar.GetComponent<Collider>();
        if (c != null) DestroyImmediate(c);
    }

'''

text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

if "private void CreatePileNumberDigitsFlat3D" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        marker = "    private Material CreatePostPileNumberBoardMaterial"
        idx = text.find(marker)
    if idx < 0:
        raise SystemExit("helper 삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("PILE번호를 캡빔 상단 눕힌 3D 막대 숫자로 수정 완료")
