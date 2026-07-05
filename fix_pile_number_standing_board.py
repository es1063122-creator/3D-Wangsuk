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

        // 캡빔 상단보다 확실히 위에 세움
        root.transform.position = worldPos + new Vector3(0f, 2.2f, 0f);

        Material boardMat = CreatePostPileNumberBoardMaterial();
        Material borderMat = CreatePostPileNumberOutlineMaterial();
        Material textMat = CreatePostPileNumberDigitMaterial();

        // 세움 번호판 배경
        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "세움번호판_" + no.ToString("000");
        board.transform.SetParent(root.transform, false);
        board.transform.localPosition = Vector3.zero;

        // 숫자판을 수직으로 세움: X 방향 폭, Y 방향 높이, Z 방향 두께
        board.transform.localScale = new Vector3(1.15f, 0.75f, 0.06f);

        Renderer br = board.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = boardMat;
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = board.GetComponent<Collider>();
        if (bc != null) DestroyImmediate(bc);

        // 번호판 테두리
        CreateNumberBoardBorder(root.transform, borderMat);

        // TextMeshPro 숫자. 숫자만 표시하므로 한글 폰트 문제 없음.
        GameObject txtObj = new GameObject("번호텍스트_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0f, -0.055f);
        txtObj.transform.localRotation = Quaternion.identity;

        TextMeshPro tmp = txtObj.AddComponent<TextMeshPro>();
        tmp.text = no.ToString();
        tmp.alignment = TextAlignmentOptions.Center;
        tmp.fontSize = 5.5f;
        tmp.color = Color.black;
        tmp.enableWordWrapping = false;
        tmp.rectTransform.sizeDelta = new Vector2(1.2f, 0.8f);

        Renderer tr = txtObj.GetComponent<Renderer>();
        if (tr != null)
        {
            tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            tr.receiveShadows = false;
            tr.sharedMaterial.renderQueue = 5000;
        }

        // 양쪽 방향에서 보이도록 뒤쪽 숫자도 생성
        GameObject txtObjBack = new GameObject("번호텍스트_BACK_" + no.ToString("000"));
        txtObjBack.transform.SetParent(root.transform, false);
        txtObjBack.transform.localPosition = new Vector3(0f, 0f, 0.055f);
        txtObjBack.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);

        TextMeshPro tmpBack = txtObjBack.AddComponent<TextMeshPro>();
        tmpBack.text = no.ToString();
        tmpBack.alignment = TextAlignmentOptions.Center;
        tmpBack.fontSize = 5.5f;
        tmpBack.color = Color.black;
        tmpBack.enableWordWrapping = false;
        tmpBack.rectTransform.sizeDelta = new Vector2(1.2f, 0.8f);

        Renderer trBack = txtObjBack.GetComponent<Renderer>();
        if (trBack != null)
        {
            trBack.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            trBack.receiveShadows = false;
            trBack.sharedMaterial.renderQueue = 5000;
        }

        // 캡빔 진행방향과 상관없이 우선 카메라에서 보기 좋은 기본 방향
        root.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
    }
'''

helpers = r'''

    private Material CreatePostPileNumberBoardMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 0.65f, 0.96f);
        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 1);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3500;
        return mat;
    }

    private void CreateNumberBoardBorder(Transform parent, Material mat)
    {
        float w = 1.22f;
        float h = 0.82f;
        float t = 0.045f;
        float z = -0.07f;

        CreateBoardBar(parent, "번호판_BORDER_TOP", new Vector3(0f, h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBoardBar(parent, "번호판_BORDER_BOTTOM", new Vector3(0f, -h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBoardBar(parent, "번호판_BORDER_LEFT", new Vector3(-w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
        CreateBoardBar(parent, "번호판_BORDER_RIGHT", new Vector3(w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
    }

    private void CreateBoardBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
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

if "private Material CreatePostPileNumberBoardMaterial" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("PILE번호를 캡빔 상단 세움 번호판 방식으로 수정 완료")
