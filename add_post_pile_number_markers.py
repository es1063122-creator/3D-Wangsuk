from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# using 추가
if "using System.Text.RegularExpressions;" not in text:
    text = text.replace("using System.IO;", "using System.IO;\nusing System.Text.RegularExpressions;")

method = r'''

    private GameObject postPileNumberGroup;

    private class PostPileNumberCandidate
    {
        public int no;
        public Vector3 pos;
        public string sourceName;
    }

    private void BuildPostPileNumberMarkers()
    {
        if (postPileNumberGroup != null)
        {
            DestroyImmediate(postPileNumberGroup);
            postPileNumberGroup = null;
        }

        GameObject pfGroup = FindGameObjectIncludingInactive("PF_HPILE");

        if (pfGroup == null)
            pfGroup = FindGameObjectIncludingInactive("PF");

        if (pfGroup == null)
            pfGroup = FindGameObjectIncludingInactive("POST_PILE");

        if (pfGroup == null)
        {
            Debug.LogWarning("[POST_PILE_NUMBER] PF_HPILE 그룹을 찾지 못했습니다.");
            return;
        }

        List<PostPileNumberCandidate> candidates = new List<PostPileNumberCandidate>();
        HashSet<int> usedNumbers = new HashSet<int>();

        // 1순위: PF_HPILE 하위 Renderer의 오브젝트 이름에서 번호 추출
        Renderer[] renderers = pfGroup.GetComponentsInChildren<Renderer>(true);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            GameObject go = r.gameObject;
            string n = go.name;

            // 너무 작은 선/보조 오브젝트는 제외
            Bounds b = r.bounds;
            if (b.size.x < 0.05f && b.size.z < 0.05f)
                continue;

            int no = ExtractPostPileNumber(n);

            if (no < 1 || no > 492)
                continue;

            if (usedNumbers.Contains(no))
                continue;

            usedNumbers.Add(no);

            candidates.Add(new PostPileNumberCandidate()
            {
                no = no,
                pos = new Vector3(b.center.x, b.max.y + 0.65f, b.center.z),
                sourceName = n
            });
        }

        // 2순위: 이름에서 번호가 충분히 안 잡히면 PF_HPILE 직계 자식 기준으로 자동 순번
        if (candidates.Count < 300)
        {
            candidates.Clear();
            usedNumbers.Clear();

            List<Transform> children = new List<Transform>();

            foreach (Transform child in pfGroup.transform)
            {
                if (child == null)
                    continue;

                Renderer[] childRenderers = child.GetComponentsInChildren<Renderer>(true);
                if (childRenderers == null || childRenderers.Length == 0)
                    continue;

                children.Add(child);
            }

            // 이름에 숫자가 있으면 이름순, 없으면 위치순
            children.Sort((a, b) =>
            {
                int na = ExtractPostPileNumber(a.name);
                int nb = ExtractPostPileNumber(b.name);

                if (na > 0 && nb > 0)
                    return na.CompareTo(nb);

                int zComp = a.position.z.CompareTo(b.position.z);
                if (zComp != 0) return zComp;

                return a.position.x.CompareTo(b.position.x);
            });

            int seq = 1;

            foreach (Transform child in children)
            {
                if (seq > 492)
                    break;

                if (!TryCalculateBounds(child.gameObject, out Bounds b))
                    continue;

                int no = ExtractPostPileNumber(child.name);
                if (no < 1 || no > 492)
                    no = seq;

                if (usedNumbers.Contains(no))
                    no = seq;

                if (usedNumbers.Contains(no))
                {
                    seq++;
                    continue;
                }

                usedNumbers.Add(no);

                candidates.Add(new PostPileNumberCandidate()
                {
                    no = no,
                    pos = new Vector3(b.center.x, b.max.y + 0.65f, b.center.z),
                    sourceName = child.name
                });

                seq++;
            }
        }

        candidates.Sort((a, b) => a.no.CompareTo(b.no));

        postPileNumberGroup = new GameObject("POST_PILE_NUMBER_MARKER");
        postPileNumberGroup.transform.SetParent(this.transform, false);

        Material discMat = CreatePostPileNumberDiscMaterial();
        Material outlineMat = CreatePostPileNumberOutlineMaterial();

        Font font = Font.CreateDynamicFontFromOSFont(new string[] { "Malgun Gothic", "맑은 고딕", "Arial" }, 72);

        int created = 0;

        foreach (var c in candidates)
        {
            if (c.no < 1 || c.no > 492)
                continue;

            CreatePostPileNumberMarker(postPileNumberGroup.transform, c.no, c.pos, discMat, outlineMat, font);
            created++;
        }

        postPileNumberGroup.SetActive(false);

        Debug.Log("[POST_PILE_NUMBER] 포스트파일 번호 원형마커 생성: " + created);
    }

    private int ExtractPostPileNumber(string name)
    {
        if (string.IsNullOrEmpty(name))
            return -1;

        MatchCollection matches = Regex.Matches(name, @"\d{1,3}");

        foreach (Match m in matches)
        {
            if (!int.TryParse(m.Value, out int no))
                continue;

            if (no >= 1 && no <= 492)
                return no;
        }

        return -1;
    }

    private void CreatePostPileNumberMarker(Transform parent, int no, Vector3 worldPos, Material discMat, Material outlineMat, Font font)
    {
        GameObject root = new GameObject("PILE_NO_" + no.ToString("000"));
        root.transform.SetParent(parent, false);
        root.transform.position = worldPos;

        // 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "원형외곽_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = Vector3.zero;
        outline.transform.localScale = new Vector3(0.78f, 0.035f, 0.78f);
        outline.GetComponent<Renderer>().sharedMaterial = outlineMat;

        // 내부 원
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "원형번호판_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = new Vector3(0f, 0.045f, 0f);
        disc.transform.localScale = new Vector3(0.64f, 0.035f, 0.64f);
        disc.GetComponent<Renderer>().sharedMaterial = discMat;

        // 숫자
        GameObject txtObj = new GameObject("번호텍스트_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.13f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = no.ToString();
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 72;
        tm.characterSize = 0.045f;
        tm.color = Color.black;

        if (font != null)
        {
            tm.font = font;
            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
                tr.sharedMaterial = font.material;
        }
    }

    private Material CreatePostPileNumberDiscMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 1f, 0.92f);
        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3050;
        return mat;
    }

    private Material CreatePostPileNumberOutlineMaterial()
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0.02f, 0.02f, 0.02f, 1f);
        return mat;
    }

    public void SetPostPileNumberMarkers(bool active)
    {
        if (postPileNumberGroup == null)
            BuildPostPileNumberMarkers();

        if (postPileNumberGroup != null)
        {
            postPileNumberGroup.SetActive(active);
            Debug.Log("[POST_PILE_NUMBER] 표시 상태: " + active);
        }
    }

    public void TogglePostPileNumberMarkers()
    {
        if (postPileNumberGroup == null)
            BuildPostPileNumberMarkers();

        if (postPileNumberGroup != null)
            postPileNumberGroup.SetActive(!postPileNumberGroup.activeSelf);
    }

'''

# 메서드 삽입 위치: FLOOR_REVIEW 함수 앞 또는 ParseHtmlColor 앞
if "BuildPostPileNumberMarkers" not in text:
    marker = "    private Color ParseHtmlColor"
    idx = text.find(marker)
    if idx < 0:
        marker = "    public void ToggleFloorReviewInfoOverlay"
        idx = text.find(marker)
    if idx < 0:
        raise SystemExit("삽입 위치를 찾지 못했습니다.")
    text = text[:idx] + method + "\n" + text[idx:]

# BuildAll 쪽에 자동 생성 호출 추가: BuildFloorReviewInfoOverlay 다음에 추가
if "BuildPostPileNumberMarkers();" not in text:
    if "BuildFloorReviewInfoOverlay();" in text:
        text = text.replace(
            "BuildFloorReviewInfoOverlay();",
            "BuildFloorReviewInfoOverlay();\n        BuildPostPileNumberMarkers();",
            1
        )
    else:
        # fallback: 마지막 Debug.Log 전 삽입 시도
        text = text.replace(
            'Debug.Log("[C605 3D] 완료',
            'BuildPostPileNumberMarkers();\n        Debug.Log("[C605 3D] 완료',
            1
        )

path.write_text(text, encoding="utf-8")
print("포스트파일 1~492 원형 번호마커 기능 추가 완료")
