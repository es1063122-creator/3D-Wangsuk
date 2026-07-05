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


new_method = r'''
    private void BuildPostPileNumberMarkers()
    {
        if (postPileNumberGroup != null)
        {
            DestroyImmediate(postPileNumberGroup);
            postPileNumberGroup = null;
        }

        List<PostPileNumberCandidate> candidates = new List<PostPileNumberCandidate>();
        HashSet<string> usedPosKeys = new HashSet<string>();

        // PF_HPILE 그룹명이 실제 Scene에 없을 수 있으므로,
        // 전체 Scene에서 PF/POST/HPILE/PILE 계열 오브젝트를 직접 찾는다.
        GameObject[] allObjects = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in allObjects)
        {
            if (go == null)
                continue;

            // Prefab/Asset 제외: Scene에 실제 배치된 오브젝트만 사용
            if (!go.scene.IsValid())
                continue;

            string n = go.name.ToUpperInvariant();

            bool isPfLike =
                n.Contains("PF") ||
                n.Contains("HPILE") ||
                n.Contains("H_PILE") ||
                n.Contains("POST") ||
                n.Contains("PILE");

            if (!isPfLike)
                continue;

            // 숫자마커 자신은 제외
            if (n.Contains("POST_PILE_NUMBER") || n.Contains("PILE_NO_") || n.Contains("NUMBER"))
                continue;

            Renderer r = go.GetComponent<Renderer>();
            if (r == null)
                continue;

            Bounds b = r.bounds;

            // 너무 작은 선/텍스트/번호는 제외
            if (b.size.y < 1.0f)
                continue;

            // 말뚝은 세로로 긴 부재이므로 y가 어느 정도 있어야 함
            if (b.size.x > 3.0f || b.size.z > 3.0f)
                continue;

            string key = Mathf.RoundToInt(b.center.x * 10f) + "_" + Mathf.RoundToInt(b.center.z * 10f);
            if (usedPosKeys.Contains(key))
                continue;

            usedPosKeys.Add(key);

            candidates.Add(new PostPileNumberCandidate()
            {
                no = -1,
                pos = new Vector3(b.center.x, b.max.y + 1.20f, b.center.z),
                sourceName = go.name
            });
        }

        if (candidates.Count == 0)
        {
            Debug.LogWarning("[POST_PILE_NUMBER] Scene에서 PF/PILE 후보를 찾지 못했습니다.");
            Debug.LogWarning("[POST_PILE_NUMBER] Hierarchy에서 실제 말뚝 오브젝트 이름을 확인해야 합니다.");
            return;
        }

        // 위치 기준 정렬.
        // 실제 번호와 완전 일치하려면 나중에 c605_pf_hpile.json 번호를 연결해야 하지만,
        // 우선 1~492 번호를 화면상 순서대로 표시한다.
        candidates.Sort((a, b) =>
        {
            int zComp = b.pos.z.CompareTo(a.pos.z);
            if (zComp != 0) return zComp;
            return a.pos.x.CompareTo(b.pos.x);
        });

        int maxCount = Mathf.Min(492, candidates.Count);

        postPileNumberGroup = new GameObject("POST_PILE_NUMBER_MARKER");
        postPileNumberGroup.transform.SetParent(this.transform, false);

        Material discMat = CreatePostPileNumberDiscMaterial();
        Material outlineMat = CreatePostPileNumberOutlineMaterial();

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Malgun Gothic", "맑은 고딕", "Arial" }, 72);

        int created = 0;

        for (int i = 0; i < maxCount; i++)
        {
            int no = i + 1;
            CreatePostPileNumberMarker(postPileNumberGroup.transform, no, candidates[i].pos, discMat, outlineMat, font);
            created++;
        }

        postPileNumberGroup.SetActive(false);

        Debug.Log("[POST_PILE_NUMBER] Scene 검색 후보 수: " + candidates.Count);
        Debug.Log("[POST_PILE_NUMBER] 포스트파일 번호 원형마커 생성: " + created);
    }
'''

text = replace_method(text, "private void BuildPostPileNumberMarkers()", new_method)

path.write_text(text, encoding="utf-8")
print("POST_PILE_NUMBER Scene 전체 검색 방식으로 수정 완료")
