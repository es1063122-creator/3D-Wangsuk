from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

helper = r'''

    // WebGL/공개용 시각 보정:
    // PF/CIP 안쪽은 실제 굴착 바닥처럼 낮추고,
    // PF/CIP 바깥쪽은 상단캡 높이에 맞춰 땅 위 기준으로 보이게 한다.
    private void ApplyInsideBottomOutsideCapHeight(string groupName)
    {
        GameObject group = GameObject.Find(groupName);
        if (group == null)
        {
            Debug.LogWarning("[INSIDE_OUTSIDE_HEIGHT] 그룹 없음: " + groupName);
            return;
        }

        Bounds pfBounds;
        if (!TryGetInsideOutsideReferenceBounds(out pfBounds))
        {
            Debug.LogWarning("[INSIDE_OUTSIDE_HEIGHT] PF/CIP 기준 Bounds 없음: " + groupName);
            return;
        }

        Bounds bottomBounds;
        float bottomY = -8.0f;

        if (TryCalculateBounds(GameObject.Find("EXCAVATION_BOTTOM"), out bottomBounds))
            bottomY = bottomBounds.max.y + 0.10f;
        else if (TryCalculateBounds(GameObject.Find("BOTTOM_EL_ZONE"), out bottomBounds))
            bottomY = bottomBounds.max.y + 0.10f;
        else
            bottomY = pfBounds.min.y - 8.0f;

        float capY = pfBounds.max.y + 0.18f;

        // PF 외곽보다 살짝 안쪽을 굴착부로 판단.
        // 너무 타이트하면 바깥쪽으로 분류되므로 margin을 둔다.
        float marginX = Mathf.Max(1.0f, pfBounds.size.x * 0.035f);
        float marginZ = Mathf.Max(1.0f, pfBounds.size.z * 0.035f);

        int insideCount = 0;
        int outsideCount = 0;

        Renderer[] renderers = group.GetComponentsInChildren<Renderer>(true);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            Transform t = r.transform;
            Vector3 p = t.position;

            bool inside =
                p.x > pfBounds.min.x + marginX &&
                p.x < pfBounds.max.x - marginX &&
                p.z > pfBounds.min.z + marginZ &&
                p.z < pfBounds.max.z - marginZ;

            float targetY = inside ? bottomY : capY;

            // 바닥/도면 계열은 얇은 면과 선이 많아서 월드 Y만 이동
            t.position = new Vector3(p.x, targetY, p.z);

            if (inside) insideCount++;
            else outsideCount++;
        }

        Debug.Log("[INSIDE_OUTSIDE_HEIGHT] " + groupName +
                  " 적용 완료 / inside=" + insideCount +
                  " bottomY=" + bottomY.ToString("F2") +
                  " / outside=" + outsideCount +
                  " capY=" + capY.ToString("F2"));
    }

    private bool TryGetInsideOutsideReferenceBounds(out Bounds bounds)
    {
        string[] names = new string[]
        {
            "CIP",
            "PF",
            "PF_HPILE",
            "WALE",
            "WALE_SPEC_REVIEW"
        };

        foreach (string n in names)
        {
            GameObject go = GameObject.Find(n);
            if (go != null && TryCalculateBounds(go, out bounds))
                return true;
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }

    public void ReapplyBottomReviewDepthEffect()
    {
        ApplyInsideBottomOutsideCapHeight("FLOOR_REVIEW_INFO");
        ApplyInsideBottomOutsideCapHeight("PLAN_VECTOR_OVERLAY");
        ApplyInsideBottomOutsideCapHeight("FINAL_BOTTOM_STEP");
        ApplyInsideBottomOutsideCapHeight("PLAN_OVERLAY");

        Debug.Log("[INSIDE_OUTSIDE_HEIGHT] 바닥검토/동자리/최종바닥 깊이감 재적용 완료");
    }

'''

if "ApplyInsideBottomOutsideCapHeight" not in text:
    insert_at = text.rfind("\n    private Shader GetWebSafeShader()")
    if insert_at < 0:
        insert_at = text.rfind("\n}")
    if insert_at < 0:
        raise SystemExit("클래스 끝 위치를 찾지 못했습니다.")
    text = text[:insert_at] + helper + text[insert_at:]
    print("inside/outside 높이 보정 함수 추가 완료")
else:
    print("inside/outside 높이 보정 함수가 이미 있습니다.")

path.write_text(text, encoding="utf-8")
