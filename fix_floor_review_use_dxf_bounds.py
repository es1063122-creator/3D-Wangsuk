from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# FloorReviewDxfBounds 클래스 추가
if "class FloorReviewDxfBounds" not in text:
    marker = "public class WangsukFullModelBuilder"
    insert = r'''
[System.Serializable]
public class FloorReviewDxfBounds
{
    public string name;
    public string source;
    public float min_x;
    public float max_x;
    public float min_y;
    public float max_y;
    public int count;
}

'''
    text = text.replace(marker, insert + marker)

# BuildFloorReviewInfoOverlay 안의 라벨 min/max 계산 부분을 DXF Bounds JSON 사용으로 교체
old = r'''
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
'''

new = r'''
        // C-605 전체 도면 DXF 좌표 범위 기준으로 라벨 위치 변환
        float minX = -16050000f;
        float maxX = -15700000f;
        float minY = 3300000f;
        float maxY = 3520000f;

        string boundsPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Review", "floor_review_dxf_bounds_v1.json");
        if (File.Exists(boundsPath))
        {
            try
            {
                FloorReviewDxfBounds b = JsonUtility.FromJson<FloorReviewDxfBounds>(File.ReadAllText(boundsPath));
                if (b != null && b.count > 0)
                {
                    minX = b.min_x;
                    maxX = b.max_x;
                    minY = b.min_y;
                    maxY = b.max_y;
                    Debug.Log("[FLOOR_REVIEW_INFO] DXF Bounds 적용: " + minX + "," + maxX + "," + minY + "," + maxY);
                }
            }
            catch
            {
                Debug.LogWarning("[FLOOR_REVIEW_INFO] DXF Bounds JSON 읽기 실패. 기본값 사용");
            }
        }
'''

if old not in text:
    raise SystemExit("라벨 min/max 계산 블록을 찾지 못했습니다.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("FLOOR_REVIEW_INFO DXF Bounds 기준 좌표변환 수정 완료")
