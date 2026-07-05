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
    private void BuildElevationRulerFromModelBounds()
    {
        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
        {
            Debug.LogWarning("[ELEVATION_RULER] Wangsuk_CAD_3D_ROOT 없음");
            return;
        }

        GameObject group = GameObject.Find("ELEVATION_RULER");
        if (group == null)
        {
            group = new GameObject("ELEVATION_RULER");
            group.transform.SetParent(root.transform, false);
        }

        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);

        bool hasBounds = false;
        Bounds b = new Bounds(Vector3.zero, Vector3.zero);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            string n = r.gameObject.name.ToUpper();
            string parentName = r.transform.parent != null ? r.transform.parent.name.ToUpper() : "";

            if (n.Contains("ELEVATION_RULER") || parentName.Contains("ELEVATION_RULER"))
                continue;

            if (n.Contains("ANCHOR") || parentName.Contains("ANCHOR"))
                continue;

            if (r.GetComponent<TextMesh>() != null)
                continue;

            if (n.Contains("TEXT") || n.Contains("LABEL") || n.Contains("PILE_NO") || n.Contains("EL_"))
                continue;

            if (!hasBounds)
            {
                b = r.bounds;
                hasBounds = true;
            }
            else
            {
                b.Encapsulate(r.bounds);
            }
        }

        if (!hasBounds)
        {
            Debug.LogWarning("[ELEVATION_RULER] Bounds 계산 실패");
            return;
        }

        float bottomY = b.min.y;
        float topY = b.max.y;
        float height = topY - bottomY;

        if (height <= 0.1f)
        {
            Debug.LogWarning("[ELEVATION_RULER] 높이 계산값 이상: " + height);
            return;
        }

        // 실제 PF 중심선을 기준으로 4개 기준자 위치를 잡는다.
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup("c605_pf_hpile.json");
        List<Vector3> pfCenters = new List<Vector3>();

        if (pfData != null && pfData.entities != null)
        {
            foreach (var pf in pfData.entities)
            {
                List<Vector3> pts = ConvertEntityPoints(pf, bottomY);
                if (pts == null || pts.Count == 0)
                    continue;

                Vector3 sum = Vector3.zero;
                foreach (var p in pts)
                    sum += p;

                pfCenters.Add(sum / pts.Count);
            }
        }

        Vector3 modelCenter = b.center;

        Vector3[] positions;
        string[] names = new string[]
        {
            "LEFT_BOTTOM",
            "RIGHT_BOTTOM",
            "LEFT_TOP",
            "RIGHT_TOP"
        };

        if (pfCenters.Count >= 10)
        {
            Vector3 pfCenter = Vector3.zero;
            foreach (var p in pfCenters)
                pfCenter += p;
            pfCenter /= pfCenters.Count;

            // 4방향 실제 PF 외곽 대표점 선택
            Vector3 lb = FindPfCornerPoint(pfCenters, pfCenter, -1f, -1f);
            Vector3 rb = FindPfCornerPoint(pfCenters, pfCenter,  1f, -1f);
            Vector3 lt = FindPfCornerPoint(pfCenters, pfCenter, -1f,  1f);
            Vector3 rt = FindPfCornerPoint(pfCenters, pfCenter,  1f,  1f);

            float nearOffset = 0.90f; // 포스트파일 바로 옆 여유거리. 더 붙이려면 0.55f

            positions = new Vector3[]
            {
                PushRulerOutside(lb, pfCenter, bottomY, nearOffset),
                PushRulerOutside(rb, pfCenter, bottomY, nearOffset),
                PushRulerOutside(lt, pfCenter, bottomY, nearOffset),
                PushRulerOutside(rt, pfCenter, bottomY, nearOffset)
            };

            modelCenter = pfCenter;

            Debug.Log("[ELEVATION_RULER] PF 기준 위치 적용 / PF count = " + pfCenters.Count + " / nearOffset = " + nearOffset);
        }
        else
        {
            // PF 데이터 실패 시 기존 Bounds 방식 fallback
            float offset = 1.10f;
            positions = new Vector3[]
            {
                new Vector3(b.min.x - offset, bottomY, b.min.z - offset),
                new Vector3(b.max.x + offset, bottomY, b.min.z - offset),
                new Vector3(b.min.x - offset, bottomY, b.max.z + offset),
                new Vector3(b.max.x + offset, bottomY, b.max.z + offset)
            };

            Debug.LogWarning("[ELEVATION_RULER] PF 기준 위치 실패. Bounds 기준 fallback 적용");
        }

        Material poleMat = CreateElevationRulerOpaqueMaterial(Color.white);
        Material tickMat = CreateElevationRulerOpaqueMaterial(Color.black);
        Material boardMat = CreateElevationRulerOpaqueMaterial(Color.white);
        Material zeroMat = CreateElevationRulerOpaqueMaterial(new Color(1.0f, 0.05f, 0.02f, 1f));
        Material capMat = CreateElevationRulerOpaqueMaterial(new Color(0.00f, 0.65f, 0.20f, 1f));

        for (int i = 0; i < positions.Length; i++)
        {
            BuildOneElevationRuler(group, positions[i], names[i], modelCenter, bottomY, topY, height, poleMat, tickMat, boardMat, zeroMat, capMat);
        }

        group.SetActive(true);

        Debug.Log("========== ELEVATION_RULER 생성 ==========");
        Debug.Log("[ELEVATION_RULER] 모델 Bounds min = " + b.min + " / max = " + b.max);
        Debug.Log("[ELEVATION_RULER] 토공바닥 기준 0m Y = " + bottomY);
        Debug.Log("[ELEVATION_RULER] 최상단 포스트/캡 Y = " + topY);
        Debug.Log("[ELEVATION_RULER] 표시 높이 = " + height + "m");
        Debug.Log("[ELEVATION_RULER] PF 외곽 4지점 근접 배치 완료");
        Debug.Log("==========================================");
    }

    private Vector3 FindPfCornerPoint(List<Vector3> centers, Vector3 center, float sx, float sz)
    {
        Vector3 best = centers[0];
        float bestScore = float.MinValue;

        foreach (var p in centers)
        {
            float dx = p.x - center.x;
            float dz = p.z - center.z;

            // sx/sz 방향으로 가장 멀리 있는 실제 PF점 선택
            float score = dx * sx + dz * sz;

            if (score > bestScore)
            {
                bestScore = score;
                best = p;
            }
        }

        return best;
    }

    private Vector3 PushRulerOutside(Vector3 pfPoint, Vector3 center, float bottomY, float offset)
    {
        Vector3 outward = pfPoint - center;
        outward.y = 0f;

        if (outward.sqrMagnitude < 0.001f)
            outward = Vector3.forward;

        outward.Normalize();

        return new Vector3(pfPoint.x, bottomY, pfPoint.z) + outward * offset;
    }
'''

text = replace_method(text, "private void BuildElevationRulerFromModelBounds", new_build)

path.write_text(text, encoding="utf-8")
print("높이 기준자 4개 모두 PF 외곽점 기준으로 근접 배치 수정 완료")
