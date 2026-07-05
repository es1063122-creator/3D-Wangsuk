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


new_build = r'''
    private void BuildFloorReviewInfoOverlay()
    {
        if (floorReviewInfoGroup != null)
        {
            DestroyImmediate(floorReviewInfoGroup);
            floorReviewInfoGroup = null;
        }

        string jsonPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Review", "floor_review_info_matched_v2.json");

        if (!File.Exists(jsonPath))
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] JSON 없음: " + jsonPath);
            return;
        }

        string json = File.ReadAllText(jsonPath);
        FloorReviewMatchedRoot root = JsonUtility.FromJson<FloorReviewMatchedRoot>(json);

        if (root == null || root.items == null || root.items.Length == 0)
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] 표시할 항목 없음");
            return;
        }

        floorReviewInfoGroup = new GameObject("FLOOR_REVIEW_INFO");
        floorReviewInfoGroup.transform.SetParent(this.transform, false);

        // 라벨 DXF 좌표 범위
        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minY = float.MaxValue;
        float maxY = float.MinValue;

        foreach (var item in root.items)
        {
            if (item.dxf_x < minX) minX = item.dxf_x;
            if (item.dxf_x > maxX) maxX = item.dxf_x;
            if (item.dxf_y < minY) minY = item.dxf_y;
            if (item.dxf_y > maxY) maxY = item.dxf_y;
        }

        // 실제 도면/동자리 그룹 Bounds에 맞춰 배치
        Bounds targetBounds;
        bool hasTargetBounds = TryGetFloorReviewTargetBounds(out targetBounds);

        if (!hasTargetBounds)
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] PLAN_VECTOR_OVERLAY Bounds를 못 찾아 임시 좌표 사용");
            targetBounds = new Bounds(new Vector3(65.45f, 0f, 202.5f), new Vector3(180f, 1f, 220f));
        }

        foreach (var item in root.items)
        {
            Vector3 pos = MapFloorReviewDxfToWorld(
                item.dxf_x,
                item.dxf_y,
                minX,
                maxX,
                minY,
                maxY,
                targetBounds
            );

            CreateFloorReviewMarker(floorReviewInfoGroup.transform, item, pos);
        }

        floorReviewInfoGroup.SetActive(false);

        Debug.Log("[FLOOR_REVIEW_INFO] 바닥검토 라벨 생성 완료: " + root.items.Length);
        Debug.Log("[FLOOR_REVIEW_INFO] targetBounds center=" + targetBounds.center + " size=" + targetBounds.size);
    }
'''

new_marker = r'''
    private void CreateFloorReviewMarker(Transform parent, FloorReviewItem item, Vector3 pos)
    {
        GameObject root = new GameObject("FLOOR_REVIEW_" + item.label);
        root.transform.SetParent(parent, false);
        root.transform.position = pos;

        Color fill = ParseHtmlColor(item.fill_color, new Color(0.2f, 1f, 0.8f, 0.26f));
        Color outline = ParseHtmlColor(item.outline_color, Color.white);
        Color bg = ParseHtmlColor(item.label_bg_color, new Color(0f, 0f, 0f, 0.82f));

        fill.a = 0.24f;
        bg.a = 0.86f;

        Vector3 plateSize = GetFloorReviewPlateSize(item.category);

        // 반투명 바닥판
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "색상영역_" + item.label;
        plate.transform.SetParent(root.transform, false);
        plate.transform.localPosition = Vector3.zero;
        plate.transform.localScale = plateSize;

        Renderer pr = plate.GetComponent<Renderer>();
        pr.sharedMaterial = CreateTransparentMat(fill);

        // 외곽선
        CreateFloorReviewOutline(root.transform, outline, plateSize);

        // 라벨 배경 박스
        GameObject labelBg = GameObject.CreatePrimitive(PrimitiveType.Cube);
        labelBg.name = "라벨박스_" + item.label;
        labelBg.transform.SetParent(root.transform, false);
        labelBg.transform.localPosition = new Vector3(0f, 0.16f, 0f);
        labelBg.transform.localScale = new Vector3(plateSize.x * 0.92f, 0.05f, Mathf.Max(1.6f, plateSize.z * 0.45f));

        Renderer br = labelBg.GetComponent<Renderer>();
        br.sharedMaterial = CreateTransparentMat(bg);

        // 한글 깨짐 방지를 위해 TextMeshPro 대신 Windows 동적 폰트 사용
        GameObject txtObj = new GameObject("라벨텍스트_" + item.label);
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.24f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = string.IsNullOrEmpty(item.display_label) ? item.label : item.display_label;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 72;
        tm.characterSize = 0.095f;
        tm.color = Color.white;

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Malgun Gothic", "맑은 고딕", "Arial" }, 72);
        if (font != null)
        {
            tm.font = font;
            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
                tr.sharedMaterial = font.material;
        }

        // 텍스트가 바닥면보다 위에 보이도록
        Renderer textRenderer = txtObj.GetComponent<Renderer>();
        if (textRenderer != null)
        {
            textRenderer.sortingOrder = 100;
        }
    }
'''

new_size = r'''
    private Vector3 GetFloorReviewPlateSize(string category)
    {
        // 도면 위에서 너무 커지지 않게 축소
        if (category == "building") return new Vector3(5.0f, 0.035f, 3.0f);
        if (category == "parking") return new Vector3(7.5f, 0.035f, 3.6f);
        if (category == "pump") return new Vector3(7.0f, 0.035f, 3.2f);
        if (category == "electric") return new Vector3(7.2f, 0.035f, 3.2f);
        if (category == "heat") return new Vector3(6.5f, 0.035f, 3.0f);
        if (category == "pit") return new Vector3(5.8f, 0.035f, 2.8f);
        return new Vector3(5.5f, 0.035f, 2.8f);
    }
'''

# 필수 메서드 교체
text = replace_method(text, "private void BuildFloorReviewInfoOverlay()", new_build)
text = replace_method(text, "private void CreateFloorReviewMarker", new_marker)
text = replace_method(text, "private Vector3 GetFloorReviewPlateSize", new_size)

# helper 삽입: ParseHtmlColor 앞에 추가
helpers = r'''

    private bool TryGetFloorReviewTargetBounds(out Bounds bounds)
    {
        // 바닥검토 라벨은 동자리/바닥 선형 정보와 맞춰야 하므로 PLAN_VECTOR_OVERLAY를 1순위로 사용
        string[] candidates = new string[]
        {
            "PLAN_VECTOR_OVERLAY",
            "FINAL_BOTTOM_STEP",
            "EXCAVATION_BOTTOM",
            "PLAN_OVERLAY",
            "Wangsuk_CAD_3D_ROOT"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
                return true;
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }

    private GameObject FindGameObjectIncludingInactive(string objectName)
    {
        GameObject[] all = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in all)
        {
            if (go == null)
                continue;

            if (go.name == objectName)
                return go;
        }

        return null;
    }

    private bool TryCalculateBounds(GameObject root, out Bounds bounds)
    {
        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
        bool has = false;
        bounds = new Bounds(root.transform.position, Vector3.zero);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            if (!has)
            {
                bounds = r.bounds;
                has = true;
            }
            else
            {
                bounds.Encapsulate(r.bounds);
            }
        }

        return has;
    }

    private Vector3 MapFloorReviewDxfToWorld(
        float dxfX,
        float dxfY,
        float minX,
        float maxX,
        float minY,
        float maxY,
        Bounds targetBounds)
    {
        float nx = Mathf.InverseLerp(minX, maxX, dxfX);
        float nz = Mathf.InverseLerp(minY, maxY, dxfY);

        // targetBounds 기준으로 라벨 영역을 내부 88% 정도에 배치
        float marginX = targetBounds.size.x * 0.06f;
        float marginZ = targetBounds.size.z * 0.06f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        return new Vector3(x, targetBounds.max.y + 0.35f, z);
    }

'''

if "private bool TryGetFloorReviewTargetBounds" not in text:
    marker = "    private Color ParseHtmlColor"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("ParseHtmlColor 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + text[idx:]

path.write_text(text, encoding="utf-8")
print("바닥검토 라벨 배치/한글 텍스트 수정 완료")
