from pathlib import Path
import re

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
        // 바닥검토 라벨은 도면 전체가 아니라 굴착 내부/최종바닥 영역에 맞춘다.
        // PLAN_VECTOR_OVERLAY는 외부 도로/외곽선까지 포함되어 너무 커지므로 사용하지 않는다.
        string[] candidates = new string[]
        {
            "EXCAVATION_BOTTOM",
            "FINAL_BOTTOM_STEP",
            "BOTTOM_ZONE_LINE",
            "BOTTOM_EL_ZONE",
            "SECTION_EL_TEXT"
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

        // fallback: 기존 C605 로그 기준 대략값
        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(210f, 2f, 260f));
        Debug.LogWarning("[FLOOR_REVIEW_INFO] 기준 그룹을 못 찾아 fallback Bounds 사용");
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

        // 현재 도면 방향 보정.
        // 캡처 기준으로 좌우는 유지, 상하는 유지한다.
        // 만약 다음 캡처에서 반대로 보이면 아래 둘 중 하나만 1f - 값으로 바꾸면 된다.
        // nx = 1f - nx;
        // nz = 1f - nz;

        // 라벨이 외곽 밖으로 퍼지지 않도록 내부로 압축
        float compress = 0.74f;
        nx = 0.5f + (nx - 0.5f) * compress;
        nz = 0.5f + (nz - 0.5f) * compress;

        // 굴착 바닥 Bounds 안쪽 여유
        float marginX = targetBounds.size.x * 0.10f;
        float marginZ = targetBounds.size.z * 0.10f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 도면선 위에 살짝 띄우기
        float y = targetBounds.max.y + 0.45f;

        return new Vector3(x, y, z);
    }
'''

new_size = r'''
    private Vector3 GetFloorReviewPlateSize(string category)
    {
        // 라벨 박스가 도면을 가리지 않도록 축소
        if (category == "building") return new Vector3(3.8f, 0.035f, 2.1f);
        if (category == "parking") return new Vector3(5.8f, 0.035f, 2.6f);
        if (category == "pump") return new Vector3(5.4f, 0.035f, 2.4f);
        if (category == "electric") return new Vector3(5.8f, 0.035f, 2.4f);
        if (category == "heat") return new Vector3(5.0f, 0.035f, 2.2f);
        if (category == "pit") return new Vector3(4.4f, 0.035f, 2.1f);
        return new Vector3(4.0f, 0.035f, 2.0f);
    }
'''

text = replace_method(text, "private bool TryGetFloorReviewTargetBounds", new_try_bounds)
text = replace_method(text, "private Vector3 MapFloorReviewDxfToWorld", new_map)
text = replace_method(text, "private Vector3 GetFloorReviewPlateSize", new_size)

path.write_text(text, encoding="utf-8")
print("바닥검토 라벨 최종 배치 보정 완료")
