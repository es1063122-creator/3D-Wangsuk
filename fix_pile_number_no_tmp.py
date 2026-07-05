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

        // 캡빔 상단 위로 세움 번호판 배치
        root.transform.position = worldPos + new Vector3(0f, 2.5f, 0f);

        Material boardMat = CreatePostPileNumberBoardMaterial();
        Material borderMat = CreatePostPileNumberOutlineMaterial();

        // 노란 세움 번호판
        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "세움번호판_" + no.ToString("000");
        board.transform.SetParent(root.transform, false);
        board.transform.localPosition = Vector3.zero;
        board.transform.localScale = new Vector3(1.30f, 0.85f, 0.08f);

        Renderer br = board.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = boardMat;
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = board.GetComponent<Collider>();
        if (bc != null) DestroyImmediate(bc);

        // 테두리
        CreateNumberBoardBorder(root.transform, borderMat);

        // 앞면 숫자 - TextMeshPro 사용 안 함
        CreatePostPileNumberTextMesh(root.transform, no.ToString(), new Vector3(0f, 0f, -0.075f), Quaternion.identity, font);

        // 뒷면 숫자
        CreatePostPileNumberTextMesh(root.transform, no.ToString(), new Vector3(0f, 0f, 0.075f), Quaternion.Euler(0f, 180f, 0f), font);

        // 일단 기본 방향. 보이면 다음 단계에서 캡빔 방향에 맞춰 회전 보정.
        root.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
    }
'''

helpers = r'''

    private void CreatePostPileNumberTextMesh(Transform parent, string textValue, Vector3 localPos, Quaternion localRot, Font font)
    {
        GameObject txtObj = new GameObject("번호텍스트_" + textValue);
        txtObj.transform.SetParent(parent, false);
        txtObj.transform.localPosition = localPos;
        txtObj.transform.localRotation = localRot;
        txtObj.transform.localScale = Vector3.one;

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = textValue;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 120;
        tm.characterSize = 0.115f;
        tm.color = Color.black;
        tm.richText = false;

        Font useFont = font;
        if (useFont == null)
            useFont = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 120);

        if (useFont != null)
        {
            tm.font = useFont;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(useFont.material);
                textMat.color = Color.black;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }

'''

text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

if "private void CreatePostPileNumberTextMesh" not in text:
    marker = "    private Material CreatePostPileNumberBoardMaterial"
    idx = text.find(marker)
    if idx < 0:
        marker = "    private Material CreatePostPileNumberDiscMaterial"
        idx = text.find(marker)
    if idx < 0:
        raise SystemExit("helper 삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

# TMP 사용 잔여 코드가 있으면 이번 PILE번호 함수에서는 안 쓰도록 됨.
path.write_text(text, encoding="utf-8")
print("PILE번호 TextMeshPro 제거 및 TextMesh 세움 번호판 수정 완료")
