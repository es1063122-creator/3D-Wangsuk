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


# 1) 카메라 바라보기 컴포넌트 추가
if "class PostPileNumberBillboard" not in text:
    marker = "public class WangsukFullModelBuilder"
    insert = r'''
public class PostPileNumberBillboard : MonoBehaviour
{
    private Camera cam;

    private void LateUpdate()
    {
        if (cam == null)
            cam = Camera.main;

        if (cam == null)
            return;

        Vector3 dir = transform.position - cam.transform.position;

        if (dir.sqrMagnitude < 0.001f)
            return;

        transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);
    }
}

'''
    text = text.replace(marker, insert + marker)


# 2) 번호판 생성 메서드 교체
new_marker = r'''
    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);

        // 캡빔 상단보다 살짝 위에 띄움
        root.transform.position = worldPos + new Vector3(0f, 4.5f, 0f);

        // 항상 카메라를 바라보도록
        root.AddComponent<PostPileNumberBillboard>();

        Material boardMat = CreatePostPileNumberBillboardBoardMaterial();
        Material borderMat = CreatePostPileNumberOutlineMaterial();

        // 노란 번호판 배경
        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "카메라번호판_" + no.ToString("000");
        board.transform.SetParent(root.transform, false);
        board.transform.localPosition = Vector3.zero;
        board.transform.localScale = new Vector3(1.10f, 0.62f, 0.055f);

        Renderer br = board.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = boardMat;
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = board.GetComponent<Collider>();
        if (bc != null) DestroyImmediate(bc);

        // 검은 테두리
        CreateBillboardBoardBorder(root.transform, borderMat);

        // 앞면 숫자
        CreatePostPileBillboardText(root.transform, no.ToString(), new Vector3(0f, -0.035f, -0.060f), Quaternion.identity, font);

        // 뒷면 숫자도 만들어서 어느 방향에서도 보이게
        CreatePostPileBillboardText(root.transform, no.ToString(), new Vector3(0f, -0.035f, 0.060f), Quaternion.Euler(0f, 180f, 0f), font);
    }
'''

helpers = r'''

    private Material CreatePostPileNumberBillboardBoardMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 0.92f, 0.15f, 1f);
        mat.renderQueue = 4500;
        return mat;
    }

    private void CreateBillboardBoardBorder(Transform parent, Material mat)
    {
        float w = 1.18f;
        float h = 0.70f;
        float t = 0.045f;
        float z = -0.070f;

        CreateBillboardBorderBar(parent, "번호판_TOP", new Vector3(0f, h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBillboardBorderBar(parent, "번호판_BOTTOM", new Vector3(0f, -h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBillboardBorderBar(parent, "번호판_LEFT", new Vector3(-w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
        CreateBillboardBorderBar(parent, "번호판_RIGHT", new Vector3(w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
    }

    private void CreateBillboardBorderBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
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

    private void CreatePostPileBillboardText(Transform parent, string value, Vector3 localPos, Quaternion localRot, Font font)
    {
        GameObject txtObj = new GameObject("번호텍스트_" + value);
        txtObj.transform.SetParent(parent, false);
        txtObj.transform.localPosition = localPos;
        txtObj.transform.localRotation = localRot;

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = value;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 160;
        tm.characterSize = 0.105f;
        tm.color = Color.black;
        tm.richText = false;

        Font useFont = font;
        if (useFont == null)
            useFont = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 160);

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

if "private void CreatePostPileBillboardText" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        marker = "    private Material CreatePostPileNumberBoardMaterial"
        idx = text.find(marker)
    if idx < 0:
        raise SystemExit("helper 삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("PILE번호 카메라 정면 번호판 방식으로 수정 완료")
