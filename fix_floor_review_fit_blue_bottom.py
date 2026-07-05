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

        // 시설명 20개의 DXF 좌표 범위를 기준으로 상대 배치한다.
        // C-605 전체 도면 Bounds를 쓰면 외부 도로/주기 영역 때문에 라벨이 바닥 밖으로 밀린다.
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

        // 가장자리 라벨이 바닥 경계에 붙지 않도록 원좌표 범위에 약간 여유를 준다.
        float padX = (maxX - minX) * 0.08f;
        float padY = (maxY - minY) * 0.08f;
        minX -= padX;
        maxX += padX;
        minY -= padY;
        maxY += padY;

        Bounds targetBounds;
        bool hasTargetBounds = TryGetFloorReviewTargetBounds(out targetBounds);

        if (!hasTargetBounds)
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] EXCAVATION_BOTTOM Bounds를 못 찾아 임시 좌표 사용");
            targetBounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(210f, 2f, 260f));
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

new_try_bounds = r'''
    private bool TryGetFloorReviewTargetBounds(out Bounds bounds)
    {
        // 사용자가 보는 파란 바닥 기준으로 라벨을 맞춘다.
        string[] candidates = new string[]
        {
            "EXCAVATION_BOTTOM",
            "FINAL_BOTTOM_STEP",
            "BOTTOM_ZONE_LINE",
            "BOTTOM_EL_ZONE"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[FLOOR_REVIEW_INFO] 기준 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(210f, 2f, 260f));
        Debug.LogWarning("[FLOOR_REVIEW_INFO] 파란 바닥 Bounds를 못 찾아 fallback Bounds 사용");
        return true;
    }
'''

new_map = r'''
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

        // 현재 캡처 기준 전체 배열은 맞으므로 반전하지 않는다.
        // 필요 시 아래 둘 중 하나만 활성화.
        // nx = 1f - nx;
        // nz = 1f - nz;

        // 파란 바닥 내부에 정확히 들어오도록 내부 여백 적용
        float marginX = targetBounds.size.x * 0.12f;
        float marginZ = targetBounds.size.z * 0.12f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 바닥 위로 띄우기
        float y = targetBounds.max.y + 8.00f;

        return new Vector3(x, y, z);
    }
'''

text = replace_method(text, "private void BuildFloorReviewInfoOverlay()", new_build)
text = replace_method(text, "private bool TryGetFloorReviewTargetBounds", new_try_bounds)
text = replace_method(text, "private Vector3 MapFloorReviewDxfToWorld", new_map)

path.write_text(text, encoding="utf-8")
print("바닥검토 라벨을 파란 바닥 기준으로 재배치 완료")
