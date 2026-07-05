from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 기존 ApplyInsideBottomOutsideCapHeight 함수 교체
pattern = re.compile(
    r'\n\s*private void ApplyInsideBottomOutsideCapHeight\s*\(string groupName\)\s*\{.*?\n\s*\}\s*\n\s*private bool TryGetInsideOutsideReferenceBounds',
    re.DOTALL
)

new_func = r'''

    private void ApplyInsideBottomOutsideCapHeight(string groupName)
    {
        GameObject group = GameObject.Find(groupName);
        if (group == null)
            return;

        Bounds pfBounds;
        if (!TryGetInsideOutsideReferenceBounds(out pfBounds))
        {
            Debug.LogWarning("[INSIDE_OUTSIDE_HEIGHT] PF/CIP 기준 Bounds 없음: " + groupName);
            return;
        }

        float bottomY = pfBounds.min.y - 7.5f;
        Bounds bottomBounds;

        GameObject bottomObj = GameObject.Find("EXCAVATION_BOTTOM");
        if (bottomObj != null && TryCalculateBounds(bottomObj, out bottomBounds))
            bottomY = bottomBounds.max.y + 0.25f;

        GameObject finalBottomObj = GameObject.Find("FINAL_BOTTOM_STEP");
        if (finalBottomObj != null && groupName != "FINAL_BOTTOM_STEP" && TryCalculateBounds(finalBottomObj, out bottomBounds))
            bottomY = Mathf.Min(bottomY, bottomBounds.max.y + 0.25f);

        float capY = pfBounds.max.y + 0.75f;

        // 외곽 띠를 넓게 잡는다.
        // 중앙 56%만 굴착 바닥, 외곽 22%씩은 상단캡 레벨.
        float innerMinX = pfBounds.min.x + pfBounds.size.x * 0.22f;
        float innerMaxX = pfBounds.max.x - pfBounds.size.x * 0.22f;
        float innerMinZ = pfBounds.min.z + pfBounds.size.z * 0.22f;
        float innerMaxZ = pfBounds.max.z - pfBounds.size.z * 0.22f;

        int insideCount = 0;
        int outsideCount = 0;

        Renderer[] renderers = group.GetComponentsInChildren<Renderer>(true);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            if (r.GetComponentInParent<Canvas>() != null)
                continue;

            Transform t = r.transform;

            Vector3 p = r.bounds.center;

            bool inside =
                p.x > innerMinX &&
                p.x < innerMaxX &&
                p.z > innerMinZ &&
                p.z < innerMaxZ;

            float targetY = inside ? bottomY : capY;

            Vector3 tp = t.position;
            t.position = new Vector3(tp.x, targetY, tp.z);

            if (inside) insideCount++;
            else outsideCount++;
        }

        Debug.Log("[INSIDE_OUTSIDE_HEIGHT_FORCE] " + groupName +
                  " / inside-bottom=" + insideCount +
                  " / outside-cap=" + outsideCount +
                  " / bottomY=" + bottomY.ToString("F2") +
                  " / capY=" + capY.ToString("F2"));
    }

    private bool TryGetInsideOutsideReferenceBounds'''

if pattern.search(text):
    text = pattern.sub(new_func, text)
    print("ApplyInsideBottomOutsideCapHeight 함수 강제형으로 교체 완료")
else:
    print("기존 함수 패턴을 못 찾아서 새 함수 추가 방식으로 진행")
    insert_at = text.rfind("\n    private Shader GetWebSafeShader()")
    if insert_at < 0:
        insert_at = text.rfind("\n}")
    helper = new_func.replace("    private bool TryGetInsideOutsideReferenceBounds", "")
    text = text[:insert_at] + helper + text[insert_at:]

# ReapplyBottomReviewDepthEffect 함수 교체
pattern2 = re.compile(
    r'\n\s*public void ReapplyBottomReviewDepthEffect\s*\(\)\s*\{.*?\n\s*\}',
    re.DOTALL
)

new_reapply = r'''

    public void ReapplyBottomReviewDepthEffect()
    {
        string[] targetNames = new string[]
        {
            "PLAN_VECTOR_OVERLAY",
            "FINAL_BOTTOM_STEP",
            "PLAN_OVERLAY",
            "FLOOR_REVIEW_INFO",
            "BOTTOM_REVIEW",
            "DONGJARI",
            "C605_PLAN_OVERLAY",
            "C605_PLAN_VECTOR_OVERLAY"
        };

        foreach (string n in targetNames)
        {
            if (GameObject.Find(n) != null)
                ApplyInsideBottomOutsideCapHeight(n);
        }

        // 이름이 정확히 다를 경우까지 대비해서 도면성 그룹 자동 검색
        Transform[] all = FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None);

        foreach (Transform tr in all)
        {
            if (tr == null)
                continue;

            string n = tr.gameObject.name.ToUpper();

            bool looksLikePlan =
                n.Contains("PLAN") ||
                n.Contains("VECTOR") ||
                n.Contains("DONG") ||
                n.Contains("BOTTOM") ||
                n.Contains("FLOOR") ||
                n.Contains("동자리") ||
                n.Contains("바닥");

            if (!looksLikePlan)
                continue;

            if (tr.GetComponentInParent<Canvas>() != null)
                continue;

            Renderer[] rs = tr.GetComponentsInChildren<Renderer>(true);
            if (rs == null || rs.Length == 0)
                continue;

            ApplyInsideBottomOutsideCapHeight(tr.gameObject.name);
        }

        Debug.Log("[INSIDE_OUTSIDE_HEIGHT_FORCE] 바닥검토/동자리/최종바닥 전체 강제 재적용 완료");
    }'''

if pattern2.search(text):
    text = pattern2.sub(new_reapply, text)
    print("ReapplyBottomReviewDepthEffect 강제형 교체 완료")
else:
    insert_at = text.rfind("\n    private Shader GetWebSafeShader()")
    if insert_at < 0:
        insert_at = text.rfind("\n}")
    text = text[:insert_at] + new_reapply + text[insert_at:]
    print("ReapplyBottomReviewDepthEffect 새로 추가 완료")

path.write_text(text, encoding="utf-8")
