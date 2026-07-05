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
    private bool TryGetPostPileNumberTargetBounds(out Bounds bounds)
    {
        // PILE 번호는 바닥이 아니라 캡빔/PF/CIP 상단 외곽 기준으로 맞춰야 한다.
        // EXCAVATION_BOTTOM은 내부 바닥 기준이라 번호가 외곽과 맞지 않는다.
        string[] candidates = new string[]
        {
            "PF",
            "PF_HPILE",
            "CIP",
            "WALE",
            "WALE_SPEC_REVIEW",
            "Wangsuk_CAD_3D_ROOT",
            "EXCAVATION_BOTTOM"
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

        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
        Debug.LogWarning("[POST_PILE_NUMBER] 기준 Bounds fallback 사용");
        return true;
    }
'''

new_map = r'''
    private Vector3 MapPostPilePointToWorld(
        float srcX,
        float srcY,
        float minX,
        float maxX,
        float minY,
        float maxY,
        Bounds targetBounds)
    {
        // PF points[] 평균좌표는 DXF 원좌표이므로 Bounds에 매핑한다.
        float nx = Mathf.InverseLerp(minX, maxX, srcX);
        float nz = Mathf.InverseLerp(minY, maxY, srcY);

        // 캡빔 외곽에 최대한 맞추기 위해 마진을 작게 둔다.
        float marginX = targetBounds.size.x * 0.005f;
        float marginZ = targetBounds.size.z * 0.005f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 이전 0.72는 너무 안쪽/왜곡이 생겼으므로 외곽에 맞게 0.92로 조정
        Vector3 c = targetBounds.center;

        float compress = 0.92f;
        x = c.x + (x - c.x) * compress;
        z = c.z + (z - c.z) * compress;

        // 캡빔 상단보다 살짝 위
        float y = targetBounds.max.y + 0.75f;

        return new Vector3(x, y, z);
    }
'''

text = replace_method(text, "private bool TryGetPostPileNumberTargetBounds", new_try_bounds)
text = replace_method(text, "private Vector3 MapPostPilePointToWorld", new_map)

path.write_text(text, encoding="utf-8")
print("PILE번호 캡빔/PF 기준 Bounds로 위치 재수정 완료")
