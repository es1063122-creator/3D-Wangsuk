from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

signature = "private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)"
idx = text.find(signature)
if idx < 0:
    raise SystemExit("CreatePostPileNumberMarker 메서드를 찾지 못했습니다.")

brace = text.find("{", idx)
if brace < 0:
    raise SystemExit("메서드 시작 중괄호를 찾지 못했습니다.")

depth = 0
end = -1
for i in range(brace, len(text)):
    if text[i] == "{":
        depth += 1
    elif text[i] == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end < 0:
    raise SystemExit("메서드 끝을 찾지 못했습니다.")

new_method = r'''
    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);
        root.transform.position = worldPos + new Vector3(0f, 0.15f, 0f);

        // 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "원형외곽_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = Vector3.zero;
        outline.transform.localRotation = Quaternion.identity;
        outline.transform.localScale = new Vector3(1.05f, 0.03f, 1.05f);

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
        disc.transform.localPosition = new Vector3(0f, 0.035f, 0f);
        disc.transform.localRotation = Quaternion.identity;
        disc.transform.localScale = new Vector3(0.82f, 0.025f, 0.82f);

        Renderer discRenderer = disc.GetComponent<Renderer>();
        if (discRenderer != null)
        {
            discRenderer.sharedMaterial = discMat;
            discRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            discRenderer.receiveShadows = false;
        }

        Collider discCol = disc.GetComponent<Collider>();
        if (discCol != null) DestroyImmediate(discCol);

        // 숫자 텍스트
        GameObject txtObj = new GameObject("번호텍스트_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.14f, 0f);

        // 핵심: 위를 보도록 -90
        txtObj.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = no.ToString();
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 120;
        tm.characterSize = 0.12f;
        tm.color = Color.black;
        tm.richText = false;

        if (font != null)
        {
            tm.font = font;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.black;
                textMat.renderQueue = 4000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }

        // 뒤집힘/가독성 대비용 보조 텍스트 하나 더
        GameObject txtObj2 = new GameObject("번호텍스트_BACK_" + no.ToString("000"));
        txtObj2.transform.SetParent(root.transform, false);
        txtObj2.transform.localPosition = new Vector3(0f, 0.145f, 0f);
        txtObj2.transform.localRotation = Quaternion.Euler(-90f, 180f, 0f);

        TextMesh tm2 = txtObj2.AddComponent<TextMesh>();
        tm2.text = no.ToString();
        tm2.anchor = TextAnchor.MiddleCenter;
        tm2.alignment = TextAlignment.Center;
        tm2.fontSize = 120;
        tm2.characterSize = 0.12f;
        tm2.color = Color.black;
        tm2.richText = false;

        if (font != null)
        {
            tm2.font = font;

            Renderer tr2 = txtObj2.GetComponent<Renderer>();
            if (tr2 != null)
            {
                Material textMat2 = new Material(font.material);
                textMat2.color = Color.black;
                textMat2.renderQueue = 4000;
                tr2.sharedMaterial = textMat2;
                tr2.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr2.receiveShadows = false;
            }
        }
    }
'''

text = text[:idx] + new_method + text[end:]
path.write_text(text, encoding="utf-8")
print("CreatePostPileNumberMarker 수정 완료")
