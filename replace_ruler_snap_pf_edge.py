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
        if (n.Contains("ANCHOR") || p.Contains("ANCHOR"))
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

    // 핵심 수정:
    // 전체 모델 Bounds가 아니라 실제 PF 중심선 범위를 기준으로 기준자를 붙인다.
    WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup("c605_pf_hpile.json");

    float minX = modelBounds.min.x;
    float maxX = modelBounds.max.x;
    float minZ = modelBounds.min.z;
    float maxZ = modelBounds.max.z;
    Vector3 pfCenter = modelBounds.center;

    if (pfData != null && pfData.entities != null && pfData.entities.Count > 0)
    {
        bool first = true;
        Vector3 sum = Vector3.zero;
        int count = 0;

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, bottomY);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 c = Vector3.zero;
            foreach (var p in pts)
                c += p;
            c /= pts.Count;

            if (first)
            {
                minX = maxX = c.x;
                minZ = maxZ = c.z;
                first = false;
            }
            else
            {
                minX = Mathf.Min(minX, c.x);
                maxX = Mathf.Max(maxX, c.x);
                minZ = Mathf.Min(minZ, c.z);
                maxZ = Mathf.Max(maxZ, c.z);
            }

            sum += c;
            count++;
        }

        if (count > 0)
            pfCenter = sum / count;

        Debug.Log("[ELEVATION_RULER] PF 기준 Bounds 적용 / PF count = " + count);
    }
    else
    {
        Debug.LogWarning("[ELEVATION_RULER] PF JSON 없음. 모델 Bounds 기준 fallback");
    }

    int maxMeter = Mathf.CeilToInt(height);

    // 아주 가까이 붙임. 겹치면 0.06f로 올리면 됨.
    float offset = 0.03f;

    float boardWidth = 0.36f;
    float boardThickness = 0.018f;
    float textZ = -(boardThickness * 0.5f + 0.008f);

    float tickThin = 0.014f;
    float majorTickLen = 0.15f;
    float minorTickLen = 0.08f;

    float meterChar = 0.035f;
    float capChar = 0.045f;

    int meterFontSize = 34;
    int capFontSize = 42;

    Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
    if (font == null)
        font = Resources.GetBuiltinResource<Font>("Arial.ttf");

    Material whiteMat = new Material(Shader.Find("Standard"));
    whiteMat.color = Color.white;

    Material blackMat = new Material(Shader.Find("Standard"));
    blackMat.color = Color.black;

    Material redMat = new Material(Shader.Find("Standard"));
    redMat.color = Color.red;

    void SetupText(TextMesh tm, Color c)
    {
        tm.font = font;
        tm.fontStyle = FontStyle.Bold;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = c;

        MeshRenderer mr = tm.GetComponent<MeshRenderer>();
        if (mr != null && font != null)
            mr.sharedMaterial = font.material;
    }

    void CreateText(Transform parent, string name, string value, Vector3 localPos, float charSize, int fontSize, Color color)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;

        // 바깥쪽에서 정방향으로 읽히게 유지
        go.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);

        TextMesh tm = go.AddComponent<TextMesh>();
        tm.text = value;
        tm.characterSize = charSize;
        tm.fontSize = fontSize;
        SetupText(tm, color);
    }

    void CreateRuler(string rulerName, Vector3 basePos, Vector3 outward)
    {
        GameObject ruler = new GameObject(rulerName);
        ruler.transform.SetParent(group.transform, false);
        ruler.transform.position = new Vector3(basePos.x, bottomY, basePos.z);
        ruler.transform.rotation = Quaternion.LookRotation(outward, Vector3.up);

        GameObject panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
        panel.name = "Panel";
        panel.transform.SetParent(ruler.transform, false);
        panel.transform.localPosition = new Vector3(0f, height * 0.5f, 0f);
        panel.transform.localRotation = Quaternion.identity;
        panel.transform.localScale = new Vector3(boardWidth, height + 0.20f, boardThickness);
        panel.GetComponent<MeshRenderer>().sharedMaterial = whiteMat;
        DestroyImmediate(panel.GetComponent<Collider>());

        GameObject spine = GameObject.CreatePrimitive(PrimitiveType.Cube);
        spine.name = "Spine";
        spine.transform.SetParent(ruler.transform, false);
        spine.transform.localPosition = new Vector3(0f, height * 0.5f, -0.004f);
        spine.transform.localRotation = Quaternion.identity;
        spine.transform.localScale = new Vector3(0.012f, height, 0.008f);
        spine.GetComponent<MeshRenderer>().sharedMaterial = blackMat;
        DestroyImmediate(spine.GetComponent<Collider>());

        for (int m = 0; m <= maxMeter; m++)
        {
            float y = Mathf.Min((float)m, height);
            float tickLen = (m == 0 || m == maxMeter || m % 5 == 0) ? majorTickLen : minorTickLen;

            GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tick.name = "Tick_" + m;
            tick.transform.SetParent(ruler.transform, false);
            tick.transform.localPosition = new Vector3(0f, y, -0.005f);
            tick.transform.localRotation = Quaternion.identity;
            tick.transform.localScale = new Vector3(tickLen, tickThin, 0.008f);
            tick.GetComponent<MeshRenderer>().sharedMaterial = (m == 0) ? redMat : blackMat;
            DestroyImmediate(tick.GetComponent<Collider>());

            CreateText(
                ruler.transform,
                "Text_" + m,
                m.ToString() + "m",
                new Vector3(0f, y, textZ),
                meterChar,
                meterFontSize,
                (m == 0) ? Color.red : Color.black
            );
        }

        CreateText(
            ruler.transform,
            "CapText",
            "CAP " + height.ToString("0.0") + "m",
            new Vector3(0f, height + 0.13f, textZ),
            capChar,
            capFontSize,
            new Color(0.0f, 0.78f, 0.16f, 1f)
        );
    }

    // PF 외곽 바로 옆 4면 중앙
    Vector3 leftCenter   = new Vector3(minX - offset, 0f, pfCenter.z);
    Vector3 rightCenter  = new Vector3(maxX + offset, 0f, pfCenter.z);
    Vector3 bottomCenter = new Vector3(pfCenter.x, 0f, minZ - offset);
    Vector3 topCenter    = new Vector3(pfCenter.x, 0f, maxZ + offset);

    CreateRuler("RULER_LEFT",   leftCenter,   Vector3.left);
    CreateRuler("RULER_RIGHT",  rightCenter,  Vector3.right);
    CreateRuler("RULER_BOTTOM", bottomCenter, Vector3.back);
    CreateRuler("RULER_TOP",    topCenter,    Vector3.forward);

    group.SetActive(true);

    Debug.Log("========== ELEVATION_RULER PF 밀착 재생성 ==========");
    Debug.Log("[ELEVATION_RULER] PF minX/maxX/minZ/maxZ = " + minX + " / " + maxX + " / " + minZ + " / " + maxZ);
    Debug.Log("[ELEVATION_RULER] offset = " + offset);
    Debug.Log("[ELEVATION_RULER] bottomY = " + bottomY + " / topY = " + topY + " / height = " + height);
    Debug.Log("[ELEVATION_RULER] PF 외곽 기준 아주 가까이 배치 완료");
    Debug.Log("==================================================");
}
'''

text = text[:start] + new_method + text[end:]
path.write_text(text, encoding="utf-8")
print("ELEVATION_RULER PF 외곽 밀착 기준으로 교체 완료")
