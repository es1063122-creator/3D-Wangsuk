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
    private void BuildSoilFillVolume()
    {
        if (soilFillVolumeGroup != null)
        {
            DestroyImmediate(soilFillVolumeGroup);
            soilFillVolumeGroup = null;
        }

        Bounds bottomBounds;
        if (!TryGetSoilFillBottomBounds(out bottomBounds))
        {
            Debug.LogWarning("[SOIL_FILL_VOLUME] 바닥 Bounds를 찾지 못했습니다.");
            return;
        }

        Bounds modelBounds;
        if (!TryGetSoilFillModelBounds(out modelBounds))
        {
            modelBounds = bottomBounds;
        }

        soilFillVolumeGroup = new GameObject("SOIL_FILL_VOLUME");
        soilFillVolumeGroup.transform.SetParent(this.transform, false);

        // X/Z는 굴착 내부 바닥 기준
        float innerScaleX = 0.88f;
        float innerScaleZ = 0.88f;

        float sx = bottomBounds.size.x * innerScaleX;
        float sz = bottomBounds.size.z * innerScaleZ;

        Vector3 center = bottomBounds.center;

        // Y는 전체 흙막이/모델 높이 기준으로 강제 설정
        // 캡빔 근처 상단부터 굴착저면 아래까지 층이 보이게 한다.
        float topY = modelBounds.max.y - 1.0f;
        float bottomY = bottomBounds.min.y - 8.0f;

        // 방어값: 너무 얇으면 강제로 깊이 확보
        if (Mathf.Abs(topY - bottomY) < 8.0f)
        {
            topY = modelBounds.max.y - 1.0f;
            bottomY = topY - 26.0f;
        }

        float totalDepth = Mathf.Abs(topY - bottomY);

        // 임시 검토용 지층 분할
        // 실제 지층선/EL 확인 후 나중에 조정
        float y0 = topY;
        float y1 = topY - totalDepth * 0.20f;
        float y2 = topY - totalDepth * 0.45f;
        float y3 = topY - totalDepth * 0.70f;
        float y4 = bottomY;

        CreateSoilFillLayer("매립층", center.x, center.z, sx, sz, y0, y1, new Color(0.62f, 0.36f, 0.14f, 0.18f));
        CreateSoilFillLayer("퇴적층", center.x, center.z, sx, sz, y1, y2, new Color(0.86f, 0.55f, 0.18f, 0.16f));
        CreateSoilFillLayer("풍화토", center.x, center.z, sx, sz, y2, y3, new Color(0.95f, 0.76f, 0.18f, 0.14f));
        CreateSoilFillLayer("풍화암", center.x, center.z, sx, sz, y3, y4, new Color(0.46f, 0.46f, 0.46f, 0.17f));

        // 옆면에서 층이 확실히 보이도록 단면판 추가
        CreateSoilSideBand("매립층", center.x, center.z, sx, sz, y0, y1, new Color(0.62f, 0.36f, 0.14f, 0.42f));
        CreateSoilSideBand("퇴적층", center.x, center.z, sx, sz, y1, y2, new Color(0.86f, 0.55f, 0.18f, 0.38f));
        CreateSoilSideBand("풍화토", center.x, center.z, sx, sz, y2, y3, new Color(0.95f, 0.76f, 0.18f, 0.34f));
        CreateSoilSideBand("풍화암", center.x, center.z, sx, sz, y3, y4, new Color(0.46f, 0.46f, 0.46f, 0.40f));

        soilFillVolumeGroup.SetActive(false);

        Debug.Log("[SOIL_FILL_VOLUME] 반투명 지층 볼륨 생성 완료");
        Debug.Log("[SOIL_FILL_VOLUME] bottomBounds center=" + bottomBounds.center + " size=" + bottomBounds.size);
        Debug.Log("[SOIL_FILL_VOLUME] modelBounds center=" + modelBounds.center + " size=" + modelBounds.size);
    }
'''

new_bottom_bounds = r'''
    private bool TryGetSoilFillBottomBounds(out Bounds bounds)
    {
        // X/Z 내부 범위는 굴착 바닥/최종바닥 기준
        string[] candidates = new string[]
        {
            "EXCAVATION_BOTTOM",
            "FINAL_BOTTOM_STEP",
            "BOTTOM_ZONE_LINE",
            "PLAN_VECTOR_OVERLAY"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[SOIL_FILL_VOLUME] 바닥 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }
'''

new_model_bounds = r'''
    private bool TryGetSoilFillModelBounds(out Bounds bounds)
    {
        // Y 높이는 흙막이 전체 모델 기준
        string[] candidates = new string[]
        {
            "Wangsuk_CAD_3D_ROOT",
            "CIP",
            "PF",
            "WALE_SPEC_REVIEW",
            "EXCAVATION_BOTTOM"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[SOIL_FILL_VOLUME] 높이 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }
'''

side_band_helpers = r'''

    private void CreateSoilSideBand(string layerName, float cx, float cz, float sx, float sz, float topY, float bottomY, Color color)
    {
        float h = Mathf.Abs(topY - bottomY);
        float cy = (topY + bottomY) * 0.5f;

        Material mat = CreateSoilFillTransparentMaterial(color);

        float t = 0.45f;

        // 앞/뒤/좌/우 측면 단면판
        CreateSoilSidePanel("SIDE_FRONT_" + layerName, new Vector3(cx, cy, cz + sz * 0.5f), new Vector3(sx, h, t), mat);
        CreateSoilSidePanel("SIDE_BACK_" + layerName, new Vector3(cx, cy, cz - sz * 0.5f), new Vector3(sx, h, t), mat);
        CreateSoilSidePanel("SIDE_LEFT_" + layerName, new Vector3(cx - sx * 0.5f, cy, cz), new Vector3(t, h, sz), mat);
        CreateSoilSidePanel("SIDE_RIGHT_" + layerName, new Vector3(cx + sx * 0.5f, cy, cz), new Vector3(t, h, sz), mat);
    }

    private void CreateSoilSidePanel(string name, Vector3 pos, Vector3 scale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "SOIL_FILL_" + name;
        go.transform.SetParent(soilFillVolumeGroup.transform, false);
        go.transform.position = pos;
        go.transform.localScale = scale;

        Renderer r = go.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = go.GetComponent<Collider>();
        if (c != null) DestroyImmediate(c);
    }
'''

# 기존 BuildSoilFillVolume 교체
text = replace_method(text, "private void BuildSoilFillVolume()", new_build)

# 기존 TryGetSoilFillTargetBounds가 있으면 bottom/model로 대체
if "private bool TryGetSoilFillTargetBounds" in text:
    text = replace_method(text, "private bool TryGetSoilFillTargetBounds", new_bottom_bounds + "\n\n" + new_model_bounds)
else:
    marker = "    private void CreateSoilFillLayer"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreateSoilFillLayer 위치를 찾지 못했습니다.")
    text = text[:idx] + new_bottom_bounds + "\n\n" + new_model_bounds + "\n\n" + text[idx:]

# side band helper 추가
if "private void CreateSoilSideBand" not in text:
    marker = "    private void CreateSoilFillLayer"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreateSoilFillLayer 위치를 찾지 못했습니다.")
    text = text[:idx] + side_band_helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("SOIL_FILL_VOLUME 실제 볼륨/측면 지층단면 방식으로 수정 완료")
