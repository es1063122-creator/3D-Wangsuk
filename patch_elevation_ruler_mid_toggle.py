from pathlib import Path

builder_path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
ui_path      = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")

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
        ch = src[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end < 0:
        raise SystemExit(f"끝 중괄호를 찾지 못했습니다: {signature}")

    return src[:idx] + new_method + src[end:]


def insert_before(src, anchor, block):
    idx = src.find(anchor)
    if idx < 0:
        raise SystemExit(f"삽입 기준 anchor를 찾지 못했습니다: {anchor}")
    return src[:idx] + block + "\n\n" + src[idx:]


# -----------------------------
# Builder patch
# -----------------------------
builder = builder_path.read_text(encoding="utf-8")

new_build_method = r'''
private void BuildElevationRulerFromModelBounds()
{
    GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
    if (root == null)
    {
        Debug.LogWarning("[ELEVATION_RULER] Wangsuk_CAD_3D_ROOT 없음");
        return;
    }

    GameObject group = GameObject.Find("ELEVATION_RULER");
    if (group == null)
    {
        group = new GameObject("ELEVATION_RULER");
        group.transform.SetParent(root.transform, false);
    }

    for (int i = group.transform.childCount - 1; i >= 0; i--)
        DestroyImmediate(group.transform.GetChild(i).gameObject);

    Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);

    Bounds b = new Bounds();
    bool hasBounds = false;

    foreach (Renderer r in renderers)
    {
        if (r == null) continue;

        string n = r.gameObject.name.ToUpper();
        string parentName = r.transform.parent != null ? r.transform.parent.name.ToUpper() : "";

        if (n.Contains("ELEVATION_RULER") || parentName.Contains("ELEVATION_RULER"))
            continue;

        if (r.GetComponent<TextMesh>() != null)
            continue;

        if (!hasBounds)
        {
            b = r.bounds;
            hasBounds = true;
        }
        else
        {
            b.Encapsulate(r.bounds);
        }
    }

    if (!hasBounds)
    {
        Debug.LogWarning("[ELEVATION_RULER] Bounds 계산 실패");
        return;
    }

    float bottomY = b.min.y;
    float topY = b.max.y;
    float height = topY - bottomY;

    if (height <= 0.1f)
    {
        Debug.LogWarning("[ELEVATION_RULER] 높이 계산값 이상: " + height);
        return;
    }

    Vector3 center = b.center;

    // 기존보다 훨씬 가까이, 그리고 꼭지점이 아니라 각 변의 중앙
    float sideOffsetX = Mathf.Max(1.4f, b.size.x * 0.012f);
    float sideOffsetZ = Mathf.Max(1.4f, b.size.z * 0.012f);

    Vector3 leftBase   = new Vector3(b.min.x - sideOffsetX, bottomY, center.z);
    Vector3 rightBase  = new Vector3(b.max.x + sideOffsetX, bottomY, center.z);
    Vector3 frontBase  = new Vector3(center.x, bottomY, b.min.z - sideOffsetZ);
    Vector3 backBase   = new Vector3(center.x, bottomY, b.max.z + sideOffsetZ);

    CreateElevationRulerSide(group.transform, "LEFT",  leftBase,  Vector3.left,    bottomY, topY);
    CreateElevationRulerSide(group.transform, "RIGHT", rightBase, Vector3.right,   bottomY, topY);
    CreateElevationRulerSide(group.transform, "FRONT", frontBase, Vector3.back,    bottomY, topY);
    CreateElevationRulerSide(group.transform, "BACK",  backBase,  Vector3.forward, bottomY, topY);

    group.SetActive(false);

    Debug.Log("========== ELEVATION_RULER 생성 ==========");
    Debug.Log("[ELEVATION_RULER] 모델 Bounds min = " + b.min + " / max = " + b.max);
    Debug.Log("[ELEVATION_RULER] 토공바닥 기준 0m Y = " + bottomY);
    Debug.Log("[ELEVATION_RULER] 최상단 포스트/캡 Y = " + topY);
    Debug.Log("[ELEVATION_RULER] 표시 높이 = " + height + "m");
    Debug.Log("[ELEVATION_RULER] 위치 = 각 변 중앙 / 버튼 토글 방식");
    Debug.Log("==========================================");
}
'''

new_text_method = r'''
private void CreateElevationRulerText(GameObject parent, string text, Vector3 pos, Vector3 outward, float size, Color color)
{
    GameObject obj = new GameObject("HEIGHT_TEXT_" + text);
    obj.transform.SetParent(parent.transform, false);
    obj.transform.position = pos;

    TextMesh tm = obj.AddComponent<TextMesh>();
    tm.text = text;
    tm.fontSize = 220;
    tm.characterSize = size;
    tm.anchor = TextAnchor.MiddleCenter;
    tm.alignment = TextAlignment.Center;
    tm.color = color;
    tm.richText = false;
    tm.fontStyle = FontStyle.Bold;

    Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Arial", "Malgun Gothic", "맑은 고딕" }, 220);
    if (font != null)
    {
        tm.font = font;
        MeshRenderer mr = obj.GetComponent<MeshRenderer>();
        if (mr != null)
        {
            mr.sharedMaterial = font.material;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }
    }

    // 숫자 방향 다시 반대로 회전
    obj.transform.rotation = Quaternion.LookRotation(-outward, Vector3.up);
}
'''

helper_block = r'''
private void CreateElevationRulerSide(Transform parent, string sideName, Vector3 basePos, Vector3 outward, float bottomY, float topY)
{
    GameObject side = new GameObject("RULER_" + sideName);
    side.transform.SetParent(parent, false);

    float totalHeight = topY - bottomY;

    float panelWidth = 1.55f;
    float panelDepth = 0.04f;
    float tickWidth = 0.34f;
    float tickHeight = 0.025f;
    float tickDepth = 0.025f;
    float textOffset = 0.06f;
    float labelSize = 0.16f;

    Quaternion rot = Quaternion.LookRotation(outward, Vector3.up);
    Vector3 panelCenter = new Vector3(basePos.x, (bottomY + topY) * 0.5f, basePos.z);

    Material whiteMat = new Material(Shader.Find("Standard"));
    whiteMat.color = Color.white;

    Material blackMat = new Material(Shader.Find("Standard"));
    blackMat.color = Color.black;

    Material redMat = new Material(Shader.Find("Standard"));
    redMat.color = Color.red;

    Material greenMat = new Material(Shader.Find("Standard"));
    greenMat.color = new Color(0.0f, 0.7f, 0.1f, 1f);

    // 메인 기준판
    GameObject panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
    panel.name = sideName + "_PANEL";
    panel.transform.SetParent(side.transform, false);
    panel.transform.position = panelCenter;
    panel.transform.rotation = rot;
    panel.transform.localScale = new Vector3(panelWidth, totalHeight, panelDepth);

    Renderer panelR = panel.GetComponent<Renderer>();
    if (panelR != null) panelR.material = whiteMat;

    // 1m 눈금
    int maxMeter = Mathf.CeilToInt(totalHeight);

    for (int i = 0; i <= maxMeter; i++)
    {
        float y = bottomY + i;
        if (y > topY + 0.001f) y = topY;

        Vector3 tickPos = new Vector3(basePos.x, y, basePos.z) + outward * 0.18f;

        GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
        tick.name = sideName + "_TICK_" + i;
        tick.transform.SetParent(side.transform, false);
        tick.transform.position = tickPos;
        tick.transform.rotation = rot;
        tick.transform.localScale = new Vector3(tickWidth, tickHeight, tickDepth);

        Renderer tr = tick.GetComponent<Renderer>();
        if (tr != null)
            tr.material = (i == 0 ? redMat : blackMat);

        Color tc = (i == 0) ? Color.red : Color.black;
        string label = (i == 0) ? "0m" : (i.ToString() + "m");

        Vector3 textPos = tickPos + outward * textOffset;
        CreateElevationRulerText(side, label, textPos, outward, labelSize, tc);

        if (Mathf.Abs(y - topY) < 0.001f)
            break;
    }

    // CAP 표기
    float capHeight = totalHeight;
    Vector3 capPos = new Vector3(basePos.x, topY + 0.18f, basePos.z) + outward * 0.24f;
    CreateElevationRulerText(side, "CAP " + capHeight.ToString("0.0") + "m", capPos, outward, 0.18f, new Color(0.0f, 0.65f, 0.0f, 1f));
}

public void ToggleElevationRuler()
{
    GameObject group = FindGameObjectIncludingInactive("ELEVATION_RULER");
    if (group == null)
    {
        Debug.Log("[ELEVATION_RULER] 기존 그룹 없음 -> 새로 생성");
        BuildElevationRulerFromModelBounds();
        group = FindGameObjectIncludingInactive("ELEVATION_RULER");
    }

    if (group == null)
    {
        Debug.LogWarning("[ELEVATION_RULER] 생성 실패");
        return;
    }

    bool next = !group.activeSelf;
    group.SetActive(next);
    Debug.Log("[ELEVATION_RULER] 표시 상태: " + next);
}
'''

# replace main methods
builder = replace_method(builder, "private void BuildElevationRulerFromModelBounds()", new_build_method)
builder = replace_method(builder, "private void CreateElevationRulerText(", new_text_method)

# insert helper block once
if "private void CreateElevationRulerSide(" not in builder:
    builder = insert_before(builder, "private void BuildSoilRockBandsAndLabels(", helper_block)
elif "public void ToggleElevationRuler()" not in builder:
    builder = insert_before(builder, "private void BuildSoilRockBandsAndLabels(", helper_block)

builder_path.write_text(builder, encoding="utf-8")

# -----------------------------
# UI patch
# -----------------------------
ui = ui_path.read_text(encoding="utf-8")

ui_method = r'''
    public void ToggleElevationRulerOverlay()
    {
        var b = Object.FindFirstObjectByType<WangsukFullModelBuilder>();
        if (b == null)
        {
            Debug.LogWarning("[ELEVATION_RULER_UI] WangsukFullModelBuilder를 찾지 못했습니다.");
            return;
        }

        b.ToggleElevationRuler();
        Debug.Log("[ELEVATION_RULER_UI] 버튼 클릭 -> 기준자 토글 실행");
    }
'''

if "public void ToggleElevationRulerOverlay()" not in ui:
    class_end = ui.rfind("}")
    if class_end < 0:
        raise SystemExit("WangsukViewerUI.cs 클래스 끝을 찾지 못했습니다.")
    ui = ui[:class_end] + "\n" + ui_method + "\n" + ui[class_end:]

ui_path.write_text(ui, encoding="utf-8")

print("기준자 위치/회전/토글 수정 완료")
