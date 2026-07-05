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


classes = r'''
[System.Serializable]
public class SoilLayerLevelRoot
{
    public string name;
    public string source;
    public string status;
    public string method;
    public SoilLayerLevel[] levels;
}

[System.Serializable]
public class SoilLayerLevel
{
    public string name;
    public float topEL;
    public float bottomEL;
    public float centerEL;
    public int sampleCount;
    public float[] color;
}

'''

if "class SoilLayerLevelRoot" not in text:
    marker = "public class WangsukFullModelBuilder"
    text = text.replace(marker, classes + "\n" + marker)


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

        float innerScaleX = 0.84f;
        float innerScaleZ = 0.84f;

        float sx = bottomBounds.size.x * innerScaleX;
        float sz = bottomBounds.size.z * innerScaleZ;
        Vector3 center = bottomBounds.center;

        string levelPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Review", "soil_layer_levels_from_section_v1.json");

        SoilLayerLevelRoot levelRoot = null;

        if (File.Exists(levelPath))
        {
            try
            {
                levelRoot = JsonUtility.FromJson<SoilLayerLevelRoot>(File.ReadAllText(levelPath));
                Debug.Log("[SOIL_FILL_VOLUME] 도면 기반 지층 레벨 JSON 적용: " + levelPath);
            }
            catch
            {
                Debug.LogWarning("[SOIL_FILL_VOLUME] 지층 레벨 JSON 읽기 실패. 임시 비율 사용");
            }
        }

        float topY = modelBounds.max.y - 1.0f;
        float bottomY = bottomBounds.min.y - 8.0f;

        if (Mathf.Abs(topY - bottomY) < 8.0f)
        {
            topY = modelBounds.max.y - 1.0f;
            bottomY = topY - 26.0f;
        }

        if (levelRoot != null && levelRoot.levels != null && levelRoot.levels.Length > 0)
        {
            float maxEL = float.MinValue;
            float minEL = float.MaxValue;

            foreach (var lv in levelRoot.levels)
            {
                if (lv.topEL > maxEL) maxEL = lv.topEL;
                if (lv.bottomEL < minEL) minEL = lv.bottomEL;
            }

            foreach (var lv in levelRoot.levels)
            {
                float layerTopY = ConvertSoilELToUnityY(lv.topEL, maxEL, minEL, topY, bottomY);
                float layerBottomY = ConvertSoilELToUnityY(lv.bottomEL, maxEL, minEL, topY, bottomY);

                Color color = GetSoilLayerColor(lv);

                CreateSoilFillLayer(lv.name, center.x, center.z, sx, sz, layerTopY, layerBottomY, color);

                Color sideColor = new Color(color.r, color.g, color.b, Mathf.Min(color.a + 0.20f, 0.48f));
                CreateSoilSideBand(lv.name, center.x, center.z, sx, sz, layerTopY, layerBottomY, sideColor);
            }

            Debug.Log("[SOIL_FILL_VOLUME] 도면 기반 추정 지층 레벨 적용 완료: " + levelRoot.levels.Length + "개 층");
        }
        else
        {
            float totalDepth = Mathf.Abs(topY - bottomY);

            float y0 = topY;
            float y1 = topY - totalDepth * 0.20f;
            float y2 = topY - totalDepth * 0.45f;
            float y3 = topY - totalDepth * 0.70f;
            float y4 = bottomY;

            CreateSoilFillLayer("매립층", center.x, center.z, sx, sz, y0, y1, new Color(0.62f, 0.36f, 0.14f, 0.18f));
            CreateSoilFillLayer("퇴적층", center.x, center.z, sx, sz, y1, y2, new Color(0.86f, 0.55f, 0.18f, 0.16f));
            CreateSoilFillLayer("풍화토", center.x, center.z, sx, sz, y2, y3, new Color(0.95f, 0.76f, 0.18f, 0.14f));
            CreateSoilFillLayer("풍화암", center.x, center.z, sx, sz, y3, y4, new Color(0.46f, 0.46f, 0.46f, 0.17f));

            CreateSoilSideBand("매립층", center.x, center.z, sx, sz, y0, y1, new Color(0.62f, 0.36f, 0.14f, 0.42f));
            CreateSoilSideBand("퇴적층", center.x, center.z, sx, sz, y1, y2, new Color(0.86f, 0.55f, 0.18f, 0.38f));
            CreateSoilSideBand("풍화토", center.x, center.z, sx, sz, y2, y3, new Color(0.95f, 0.76f, 0.18f, 0.34f));
            CreateSoilSideBand("풍화암", center.x, center.z, sx, sz, y3, y4, new Color(0.46f, 0.46f, 0.46f, 0.40f));

            Debug.LogWarning("[SOIL_FILL_VOLUME] 임시 비율 지층 레벨 사용");
        }

        soilFillVolumeGroup.SetActive(false);

        Debug.Log("[SOIL_FILL_VOLUME] 반투명 지층 볼륨 생성 완료");
        Debug.Log("[SOIL_FILL_VOLUME] bottomBounds center=" + bottomBounds.center + " size=" + bottomBounds.size);
        Debug.Log("[SOIL_FILL_VOLUME] modelBounds center=" + modelBounds.center + " size=" + modelBounds.size);
    }
'''

helpers = r'''

    private float ConvertSoilELToUnityY(float el, float maxEL, float minEL, float topY, float bottomY)
    {
        if (Mathf.Abs(maxEL - minEL) < 0.001f)
            return topY;

        float t = Mathf.InverseLerp(maxEL, minEL, el);
        return Mathf.Lerp(topY, bottomY, t);
    }

    private Color GetSoilLayerColor(SoilLayerLevel lv)
    {
        if (lv != null && lv.color != null && lv.color.Length >= 4)
            return new Color(lv.color[0], lv.color[1], lv.color[2], lv.color[3]);

        if (lv != null)
        {
            if (lv.name == "매립층") return new Color(0.62f, 0.36f, 0.14f, 0.20f);
            if (lv.name == "퇴적층") return new Color(0.86f, 0.55f, 0.18f, 0.18f);
            if (lv.name == "풍화토") return new Color(0.95f, 0.76f, 0.18f, 0.16f);
            if (lv.name == "풍화암") return new Color(0.46f, 0.46f, 0.46f, 0.20f);
            if (lv.name == "보통암") return new Color(0.28f, 0.28f, 0.28f, 0.22f);
        }

        return new Color(0.5f, 0.5f, 0.5f, 0.18f);
    }

'''

text = replace_method(text, "private void BuildSoilFillVolume()", new_build)

if "private float ConvertSoilELToUnityY" not in text:
    marker = "    private void CreateSoilFillLayer"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("CreateSoilFillLayer 위치를 찾지 못했습니다.")
    text = text[:idx] + helpers + "\n" + text[idx:]

path.write_text(text, encoding="utf-8")
print("SOIL_FILL_VOLUME 도면 기반 지층 레벨 JSON 적용 방식으로 수정 완료")
