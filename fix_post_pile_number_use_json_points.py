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


# JSON 클래스 추가
if "class PostPileNumberPointRoot" not in text:
    marker = "public class WangsukFullModelBuilder"
    insert = r'''
[System.Serializable]
public class PostPileNumberPointRoot
{
    public string name;
    public string source;
    public string status;
    public int count;
    public PostPileNumberPoint[] points;
}

[System.Serializable]
public class PostPileNumberPoint
{
    public int no;
    public float x;
    public float y;
    public string key_x;
    public string key_y;
}

'''
    text = text.replace(marker, insert + marker)


new_build = r'''
    private void BuildPostPileNumberMarkers()
    {
        if (postPileNumberGroup != null)
        {
            DestroyImmediate(postPileNumberGroup);
            postPileNumberGroup = null;
        }

        string jsonPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Review", "post_pile_number_points_v1.json");

        if (!File.Exists(jsonPath))
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON 없음: " + jsonPath);
            return;
        }

        PostPileNumberPointRoot root = JsonUtility.FromJson<PostPileNumberPointRoot>(File.ReadAllText(jsonPath));

        if (root == null || root.points == null || root.points.Length == 0)
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON에 point 없음");
            return;
        }

        Bounds targetBounds;
        if (!TryGetPostPileNumberTargetBounds(out targetBounds))
        {
            targetBounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
            Debug.LogWarning("[POST_PILE_NUMBER] 기준 Bounds fallback 사용");
        }

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minY = float.MaxValue;
        float maxY = float.MinValue;

        foreach (var p in root.points)
        {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.y > maxY) maxY = p.y;
        }

        // PF 원좌표 전체 범위에 약간 여유
        float padX = (maxX - minX) * 0.015f;
        float padY = (maxY - minY) * 0.015f;
        minX -= padX;
        maxX += padX;
        minY -= padY;
        maxY += padY;

        postPileNumberGroup = new GameObject("POST_PILE_NUMBER_MARKER");
        postPileNumberGroup.transform.SetParent(this.transform, false);

        Material discMat = CreatePostPileNumberDiscMaterial();
        Material outlineMat = CreatePostPileNumberOutlineMaterial();

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Malgun Gothic", "맑은 고딕", "Arial" }, 72);

        int created = 0;

        foreach (var p in root.points)
        {
            if (p.no < 1 || p.no > 492)
                continue;

            Vector3 pos = MapPostPilePointToWorld(p.x, p.y, minX, maxX, minY, maxY, targetBounds);

            CreatePostPileNumberMarker(postPileNumberGroup.transform, p.no, pos, discMat, outlineMat, font);
            created++;
        }

        postPileNumberGroup.SetActive(false);

        Debug.Log("[POST_PILE_NUMBER] JSON point count: " + root.points.Length);
        Debug.Log("[POST_PILE_NUMBER] 포스트파일 번호 원형마커 생성: " + created);
        Debug.Log("[POST_PILE_NUMBER] targetBounds center=" + targetBounds.center + " size=" + targetBounds.size);
    }
'''

new_marker = r'''
    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);
        root.transform.position = worldPos;

        // 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "원형외곽_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = Vector3.zero;
        outline.transform.localScale = new Vector3(0.95f, 0.025f, 0.95f);
        outline.GetComponent<Renderer>().sharedMaterial = outlineMat;

        // 내부 원
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "원형번호판_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = new Vector3(0f, 0.035f, 0f);
        disc.transform.localScale = new Vector3(0.78f, 0.025f, 0.78f);
        disc.GetComponent<Renderer>().sharedMaterial = discMat;

        // 숫자
        GameObject txtObj = new GameObject("번호텍스트_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.16f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = no.ToString();
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 96;
        tm.characterSize = 0.055f;
        tm.color = Color.black;

        if (font != null)
        {
            tm.font = font;
            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.black;
                tr.sharedMaterial = textMat;
            }
        }
    }
'''

helpers = r'''

    private bool TryGetPostPileNumberTargetBounds(out Bounds bounds)
    {
        string[] candidates = new string[]
        {
            "EXCAVATION_BOTTOM",
            "PLAN_VECTOR_OVERLAY",
            "FINAL_BOTTOM_STEP",
            "BOTTOM_ZONE_LINE"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[POST_PILE_NUMBER] 기준 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }

    private Vector3 MapPostPilePointToWorld(
        float srcX,
        float srcY,
        float minX,
        float maxX,
        float minY,
        float maxY,
        Bounds targetBounds)
    {
        float nx = Mathf.InverseLerp(minX, maxX, srcX);
        float nz = Mathf.InverseLerp(minY, maxY, srcY);

        // 파란 바닥과 같은 기준으로 내부 여백 적용
        float marginX = targetBounds.size.x * 0.03f;
        float marginZ = targetBounds.size.z * 0.03f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 포스트파일 상단보다 충분히 위
        float y = targetBounds.max.y + 11.00f;

        return new Vector3(x, y, z);
    }

'''

text = replace_method(text, "private void BuildPostPileNumberMarkers()", new_build)
text = replace_method(text, "private void CreatePostPileNumberMarker", new_marker)

if "private bool TryGetPostPileNumberTargetBounds" not in text:
    marker = "    private Material CreatePostPileNumberDiscMaterial"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("helper 삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("POST_PILE_NUMBER JSON 좌표 기준 생성 방식으로 교체 완료")
