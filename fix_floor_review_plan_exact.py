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


new_try_bounds = r'''
    private bool TryGetFloorReviewTargetBounds(out Bounds bounds)
    {
        // 바닥검토 라벨은 C-605 바닥 도면선 위에 정확히 올라가야 하므로
        // 굴착바닥(EXCAVATION_BOTTOM)이 아니라 PLAN_VECTOR_OVERLAY를 기준으로 한다.
        string[] candidates = new string[]
        {
            "PLAN_VECTOR_OVERLAY",
            "PLAN_OVERLAY",
            "Wangsuk_CAD_3D_ROOT"
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

        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
        Debug.LogWarning("[FLOOR_REVIEW_INFO] PLAN_VECTOR_OVERLAY를 못 찾아 fallback Bounds 사용");
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

        // C-605 DXF 원좌표를 PLAN_VECTOR_OVERLAY 전체 도면 Bounds에 그대로 대응.
        // 압축/마진을 넣으면 원래 도면 위치에서 틀어지므로 사용하지 않는다.
        float x = Mathf.Lerp(targetBounds.min.x, targetBounds.max.x, nx);
        float z = Mathf.Lerp(targetBounds.min.z, targetBounds.max.z, nz);

        // 바닥 도면선 위로 확실히 띄운다.
        float y = targetBounds.max.y + 8.00f;

        return new Vector3(x, y, z);
    }
'''

text = replace_method(text, "private bool TryGetFloorReviewTargetBounds", new_try_bounds)
text = replace_method(text, "private Vector3 MapFloorReviewDxfToWorld", new_map)

path.write_text(text, encoding="utf-8")
print("바닥검토 라벨 PLAN_VECTOR_OVERLAY 원위치 기준 수정 완료")
