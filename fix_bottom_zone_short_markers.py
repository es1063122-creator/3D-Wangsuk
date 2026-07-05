from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

start = text.find("    private void CreateBottomZoneLine(GameObject group, List<Vector3> centers, Vector3 allCenter, int pfNo, float y)")
if start < 0:
    print("CreateBottomZoneLine 함수를 찾지 못했습니다.")
else:
    brace = text.find("{", start)
    depth = 0
    end = brace

    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    new_func = r'''    private void CreateBottomZoneLine(GameObject group, List<Vector3> centers, Vector3 allCenter, int pfNo, float y)
    {
        int index = Mathf.Clamp(pfNo - 1, 0, centers.Count - 1);
        Vector3 p = centers[index];

        Vector3 inward = new Vector3(allCenter.x - p.x, 0f, allCenter.z - p.z);
        if (inward.sqrMagnitude > 0.0001f)
            inward.Normalize();

        // 바닥구분은 긴 선이 아니라 벽체 가까이의 짧은 구간 경계 마커로 표시
        Vector3 a = new Vector3(p.x, y + 0.08f, p.z) + inward * 0.35f;
        Vector3 b = new Vector3(p.x, y + 0.08f, p.z) + inward * 1.80f;

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.1f)
            return;

        GameObject line = GameObject.CreatePrimitive(PrimitiveType.Cube);
        line.name = "C605_BOTTOM_ZONE_SHORT_MARKER_P" + pfNo;
        line.transform.SetParent(group.transform, false);
        line.transform.position = (a + b) * 0.5f;
        line.transform.localScale = new Vector3(0.055f, 0.035f, len);
        line.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 1f, 0.82f);
        line.GetComponent<Renderer>().material = mat;

        // 아주 작은 P번호 라벨
        CreateBottomZoneMarkerLabel(group, "P" + pfNo.ToString("000"), b + inward * 0.25f, y + 0.18f);
    }

    private void CreateBottomZoneMarkerLabel(GameObject group, string label, Vector3 position, float y)
    {
        GameObject obj = new GameObject("C605_BOTTOM_ZONE_LABEL_" + label);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = new Vector3(position.x, y, position.z);
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 72;
        tm.characterSize = 0.035f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.white;

        Font font = Font.CreateDynamicFontFromOSFont("Arial", 72);
        if (font != null)
        {
            tm.font = font;
            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = font.material;
                mr.material.color = Color.white;
            }
        }
    }'''

    text = text[:start] + new_func + text[end:]
    print("바닥구분선을 짧은 구간 경계 마커 방식으로 교체 완료")

path.write_text(text, encoding="utf-8")
print("저장 완료")
