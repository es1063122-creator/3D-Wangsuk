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
        // PF 좌표는 DXF 원좌표이므로 Bounds에 매핑한다.
        float nx = Mathf.InverseLerp(minX, maxX, srcX);
        float nz = Mathf.InverseLerp(minY, maxY, srcY);

        float marginX = targetBounds.size.x * 0.025f;
        float marginZ = targetBounds.size.z * 0.025f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 현재 번호마커가 실제 캡빔보다 바깥으로 크게 퍼져 있음.
        // 중심 기준으로 축소해서 캡빔 상단 쪽으로 당긴다.
        Vector3 c = targetBounds.center;

        float compress = 0.72f;
        x = c.x + (x - c.x) * compress;
        z = c.z + (z - c.z) * compress;

        // 캡빔 상단 위 표시
        float y = targetBounds.max.y + 1.20f;

        return new Vector3(x, y, z);
    }
'''

text = replace_method(text, "private Vector3 MapPostPilePointToWorld", new_map)

path.write_text(text, encoding="utf-8")
print("PILE번호 위치 중심축소 보정 완료")
