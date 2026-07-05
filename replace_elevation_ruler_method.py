from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

signature = "private void BuildElevationRulerFromModelBounds()"
start = text.find(signature)
if start < 0:
    raise SystemExit("BuildElevationRulerFromModelBounds 메서드를 찾지 못했습니다.")

brace = text.find("{", start)
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
    raise SystemExit("메서드 끝 중괄호를 찾지 못했습니다.")

new_method = r'''
private void BuildElevationRulerFromModelBounds()
{
    GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
    if (root == null)
    {
        Debug.LogWarning("[ELEVATION_RULER] Wangsuk_CAD_3D_ROOT 없음");
        return;
    }

    GameObject group = FindGameObjectIncludingInactive("ELEVATION_RULER");
    if (group == null)
    {
        group = new GameObject("ELEVATION_RULER");
        group.transform.SetParent(root.transform, false);
    }

    for (int i = group.transform.childCount - 1; i >= 0; i--)
        DestroyImmediate(group.transform.GetChild(i).gameObject);

    Bounds modelBounds = new Bounds();
    bool hasBounds = false;

    Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
    foreach (Renderer r in renderers)
    {
        if (r == null) continue;

        string n = r.gameObject.name.ToUpper();
        string p = r.transform.parent != null ? r.transform.parent.name.ToUpper() : "";

        if (n.Contains("ELEVATION_RULER") || p.Contains("ELEVATION_RULER"))
            continue;
        if (n.Contains("UI") || p.Contains("UI"))
            continue;
        if (n.Contains("TEXT") || p.Contains("TEXT"))
            continue;

        if (!hasBounds)
        {
            modelBounds = r.bounds;
            hasBounds = true;
        }
        else
        {
            modelBounds.Encapsulate(r.bounds);
        }
    }

    if (!hasBounds)
    {
        Debug.LogWarning("[ELEVATION_RULER] Bounds 계산 실패");
        return;
    }

    float bottomY = modelBounds.min.y;
    GameObject bottomObj = FindGameObjectIncludingInactive("EXCAVATION_BOTTOM");
    if (bottomObj != null)
    {
        Renderer[] brs = bottomObj.GetComponentsInChildren<Renderer>(true);
        Bounds bb = new Bounds();
        bool hasBottom = false;
        foreach (Renderer r in brs)
        {
            if (r == null) continue;
            if (!hasBottom)
            {
                bb = r.bounds;
                hasBottom = true;
            }
            else
            {
                bb.Encapsulate(r.bounds);
            }
        }
        if (hasBottom)
            bottomY = bb.center.y;
    }

    float topY = modelBounds.max.y;
    float height = topY - bottomY;

    if (height <= 0.1f)
    {
        Debug.LogWarning("[ELEVATION_RULER] 높이 계산값 이상: " + height);
        return;
    }

    int maxMeter = Mathf.CeilToInt(height);

    // 기존보다 훨씬 더 가까이 붙임
    float offset = Mathf.Max(1.2f, Mathf.Max(modelBounds.size.x, modelBounds.size.z) * 0.0065f);

    // 글씨/판 크기 축소
    float boardWidth = 0.85f;
    float boardThickness = 0.05f;
    float tickHeight = 0.03f;
    float tickDepth = 0.02f;
    float majorTickLen = 0.42f;
    float minorTickLen = 0.26f;
    float meterChar = 0.12f;
    float capChar = 0.20f;
    int meterFontSize = 64;
    int capFontSize = 84;

    Material whiteMat = new Material(Shader.Find("Standard"));
    whiteMat.color = new Color(1f, 1f, 1f, 1f);

    Material blackMat = new Material(Shader.Find("Standard"));
    blackMat.color = new Color(0.06f, 0.06f, 0.06f, 1f);

    Material redMat = new Material(Shader.Find("Standard"));
    redMat.color = new Color(1f, 0.12f, 0.12f, 1f);

    Material greenMat = new Material(Shader.Find("Standard"));
    greenMat.color = new Color(0.0f, 0.78f, 0.16f, 1f);

    void ApplyTextMaterial(TextMesh tm, Color c)
    {
        MeshRenderer mr = tm.GetComponent<MeshRenderer>();
        if (mr != null)
        {
            Material m = new Material(Shader.Find("GUI/Text Shader"));
            m.color = c;
            mr.sharedMaterial = m;
        }
        tm.color = c;
    }

    void CreateText(Transform parent, string name, string value, Vector3 localPos, float charSize, int fontSize, Color color)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localRotation = Quaternion.identity;

        TextMesh tm = go.AddComponent<TextMesh>();
        tm.text = value;
        tm.characterSize = charSize;
        tm.fontSize = fontSize;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        ApplyTextMaterial(tm, color);
    }

    void CreateRuler(string rulerName, Vector3 sideCenter, Vector3 outward)
    {
        GameObject ruler = new GameObject(rulerName);
        ruler.transform.SetParent(group.transform, false);
        ruler.transform.position = new Vector3(sideCenter.x, bottomY, sideCenter.z);
        ruler.transform.rotation = Quaternion.LookRotation(outward, Vector3.up);

        GameObject panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
        panel.name = "Panel";
        panel.transform.SetParent(ruler.transform, false);
        panel.transform.localPosition = new Vector3(0f, height * 0.5f, 0f);
        panel.transform.localRotation = Quaternion.identity;
        panel.transform.localScale = new Vector3(boardWidth, height, boardThickness);
        panel.GetComponent<MeshRenderer>().sharedMaterial = whiteMat;
        DestroyImmediate(panel.GetComponent<Collider>());

        GameObject spine = GameObject.CreatePrimitive(PrimitiveType.Cube);
        spine.name = "Spine";
        spine.transform.SetParent(ruler.transform, false);
        spine.transform.localPosition = new Vector3(0f, height * 0.5f, -0.012f);
        spine.transform.localRotation = Quaternion.identity;
        spine.transform.localScale = new Vector3(0.028f, height, 0.01f);
        spine.GetComponent<MeshRenderer>().sharedMaterial = blackMat;
        DestroyImmediate(spine.GetComponent<Collider>());

        for (int m = 0; m <= maxMeter; m++)
        {
            float y = Mathf.Min((float)m, height);
            float len = (m % 5 == 0 || m == 0 || m == maxMeter) ? majorTickLen : minorTickLen;

            GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tick.name = "Tick_" + m;
            tick.transform.SetParent(ruler.transform, false);
            tick.transform.localPosition = new Vector3(0f, y, -0.015f);
            tick.transform.localRotation = Quaternion.identity;
            tick.transform.localScale = new Vector3(len, tickHeight, tickDepth);
            tick.GetComponent<MeshRenderer>().sharedMaterial = (m == 0) ? redMat : blackMat;
            DestroyImmediate(tick.GetComponent<Collider>());

            CreateText(
                ruler.transform,
                "Text_" + m,
                m.ToString() + "m",
                new Vector3(0f, y, -0.06f),
                meterChar,
                meterFontSize,
                (m == 0) ? Color.red : Color.black
            );
        }

        float capY = height + 0.45f;
        CreateText(
            ruler.transform,
            "CapText",
            "CAP " + height.ToString("0.0") + "m",
            new Vector3(0f, capY, -0.06f),
            capChar,
            capFontSize,
            new Color(0.0f, 0.78f, 0.16f, 1f)
        );
    }

    Vector3 leftCenter   = new Vector3(modelBounds.min.x - offset, 0f, modelBounds.center.z);
    Vector3 rightCenter  = new Vector3(modelBounds.max.x + offset, 0f, modelBounds.center.z);
    Vector3 bottomCenter = new Vector3(modelBounds.center.x, 0f, modelBounds.min.z - offset);
    Vector3 topCenter    = new Vector3(modelBounds.center.x, 0f, modelBounds.max.z + offset);

    // 바깥쪽에서 읽히도록 방향 지정
    CreateRuler("RULER_LEFT",   leftCenter,   Vector3.left);
    CreateRuler("RULER_RIGHT",  rightCenter,  Vector3.right);
    CreateRuler("RULER_BOTTOM", bottomCenter, Vector3.back);
    CreateRuler("RULER_TOP",    topCenter,    Vector3.forward);

    group.SetActive(true);

    Debug.Log("========== ELEVATION_RULER 재생성 ==========");
    Debug.Log("[ELEVATION_RULER] offset = " + offset);
    Debug.Log("[ELEVATION_RULER] bottomY = " + bottomY + " / topY = " + topY + " / height = " + height);
    Debug.Log("[ELEVATION_RULER] 4면 중앙 배치 / 더 가깝게 / 글씨 축소 적용 완료");
    Debug.Log("===========================================");
}
'''

text = text[:start] + new_method + text[end:]
path.write_text(text, encoding="utf-8")
print("BuildElevationRulerFromModelBounds 교체 완료")
