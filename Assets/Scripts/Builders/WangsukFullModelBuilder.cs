using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;
using TMPro;


[System.Serializable]
public class FloorReviewMatchedRoot
{
    public string name;
    public string status;
    public string source;
    public FloorReviewItem[] items;
}

[System.Serializable]
public class FloorReviewItem
{
    public string label;
    public string display_label;
    public string category;
    public string category_name;
    public string el;
    public float dxf_x;
    public float dxf_y;
    public string fill_color;
    public string outline_color;
    public string label_bg_color;
}

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


[System.Serializable]
public class PostPileNumberPointRoot
{
    public string name;
    public string source;
    public string status;
    public int count;
    public PostPileNumberPoint[] points;
}

[System.Serializable]
public class PostPileNumberPoint
{
    public int no;
    public float x;
    public float y;
    public string key_x;
    public string key_y;
}


public class PostPileNumberBillboard : MonoBehaviour
{
    private Camera cam;

    private void LateUpdate()
    {
        if (cam == null)
            cam = Camera.main;

        if (cam == null)
            return;

        Vector3 dir = transform.position - cam.transform.position;

        if (dir.sqrMagnitude < 0.001f)
            return;

        transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);
    }
}


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


public class WangsukFullModelBuilder : MonoBehaviour
{
    public ModelGroupRegistry registry;

    [Header("C-605 PF/CIP 표현")]
    public float pfLineWidth = 0.45f;
    public float pfWallHeight = 6.0f;
    public float pfWallThickness = 0.35f;

    public float cipRadius = 0.26f;
    public float cipHeight = 7.5f;

    [Header("WALE 띠장 단수")]
    public bool buildWaleLevel1 = true;
    public bool buildWaleLevel2 = true;
    public bool buildWaleLevel3 = true;

    // 기존 도면 검토값 기준
    public float waleDepth1 = 0.6f;
    public float waleDepth2 = 4.4f;
    public float waleDepth3 = 5.8f;
    [SerializeField] private float waleDepth4 = 7.2f;

    public float waleWidth = 0.42f;
    public float waleHeight = 0.28f;
    public float waleOffsetFromWall = 0.10f;

    private Material pfLineMaterial;
    private Material pfWallMaterial;
    private Material cipMaterial;
    private Material cipTopMaterial;
    private Material waleMaterial;

    
    private GameObject floorReviewInfoGroup;

    
    
    private void BuildFloorReviewInfoOverlay()
    {
        if (floorReviewInfoGroup != null)
        {
            DestroyImmediate(floorReviewInfoGroup);
            floorReviewInfoGroup = null;
        }

        string jsonPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Review", "floor_review_info_matched_v2.json");

        if (!File.Exists(jsonPath))
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] JSON 없음: " + jsonPath);
            return;
        }

        string json = File.ReadAllText(jsonPath);
        FloorReviewMatchedRoot root = JsonUtility.FromJson<FloorReviewMatchedRoot>(json);

        if (root == null || root.items == null || root.items.Length == 0)
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] 표시할 항목 없음");
            return;
        }

        floorReviewInfoGroup = new GameObject("FLOOR_REVIEW_INFO");
        floorReviewInfoGroup.transform.SetParent(this.transform, false);

        // 시설명 20개의 DXF 좌표 범위를 기준으로 상대 배치한다.
        // C-605 전체 도면 Bounds를 쓰면 외부 도로/주기 영역 때문에 라벨이 바닥 밖으로 밀린다.
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

        // 가장자리 라벨이 바닥 경계에 붙지 않도록 원좌표 범위에 약간 여유를 준다.
        float padX = (maxX - minX) * 0.08f;
        float padY = (maxY - minY) * 0.08f;
        minX -= padX;
        maxX += padX;
        minY -= padY;
        maxY += padY;

        Bounds targetBounds;
        bool hasTargetBounds = TryGetFloorReviewTargetBounds(out targetBounds);

        if (!hasTargetBounds)
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] EXCAVATION_BOTTOM Bounds를 못 찾아 임시 좌표 사용");
            targetBounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(210f, 2f, 260f));
        }

        foreach (var item in root.items)
        {
            Vector3 pos = MapFloorReviewDxfToWorld(
                item.dxf_x,
                item.dxf_y,
                minX,
                maxX,
                minY,
                maxY,
                targetBounds
            );

            CreateFloorReviewMarker(floorReviewInfoGroup.transform, item, pos);
        }

        floorReviewInfoGroup.SetActive(false);

        Debug.Log("[FLOOR_REVIEW_INFO] 바닥검토 라벨 생성 완료: " + root.items.Length);
        Debug.Log("[FLOOR_REVIEW_INFO] targetBounds center=" + targetBounds.center + " size=" + targetBounds.size);
    }



    
    private void CreateFloorReviewMarker(Transform parent, FloorReviewItem item, Vector3 pos)
    {
        GameObject root = new GameObject("FLOOR_REVIEW_" + item.label);
        root.transform.SetParent(parent, false);
        root.transform.position = pos;

        Color fill = ParseHtmlColor(item.fill_color, new Color(0.2f, 1f, 0.8f, 0.26f));
        Color outline = ParseHtmlColor(item.outline_color, Color.white);
        Color bg = ParseHtmlColor(item.label_bg_color, new Color(0f, 0f, 0f, 0.82f));

        fill.a = 0.24f;
        bg.a = 0.86f;

        Vector3 plateSize = GetFloorReviewPlateSize(item.category);

        // 반투명 바닥판
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "색상영역_" + item.label;
        plate.transform.SetParent(root.transform, false);
        plate.transform.localPosition = Vector3.zero;
        plate.transform.localScale = plateSize;

        Renderer pr = plate.GetComponent<Renderer>();
        pr.sharedMaterial = CreateTransparentMat(fill);

        // 외곽선
        CreateFloorReviewOutline(root.transform, outline, plateSize);

        // 라벨 배경 박스
        GameObject labelBg = GameObject.CreatePrimitive(PrimitiveType.Cube);
        labelBg.name = "라벨박스_" + item.label;
        labelBg.transform.SetParent(root.transform, false);
        labelBg.transform.localPosition = new Vector3(0f, 0.35f, 0f);
        labelBg.transform.localScale = new Vector3(plateSize.x * 0.92f, 0.05f, Mathf.Max(1.6f, plateSize.z * 0.45f));

        Renderer br = labelBg.GetComponent<Renderer>();
        br.sharedMaterial = CreateTransparentMat(bg);

        // 한글 깨짐 방지를 위해 TextMeshPro 대신 Windows 동적 폰트 사용
        GameObject txtObj = new GameObject("라벨텍스트_" + item.label);
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.55f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = string.IsNullOrEmpty(item.display_label) ? item.label : item.display_label;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 72;
        tm.characterSize = 0.095f;
        tm.color = Color.white;

        Font font = KoreanFontProvider.Get();
        if (font != null)
        {
            tm.font = font;
            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
                tr.sharedMaterial = font.material;
        }

        // 텍스트가 바닥면보다 위에 보이도록
        Renderer textRenderer = txtObj.GetComponent<Renderer>();
        if (textRenderer != null)
        {
            textRenderer.sortingOrder = 100;
        }
    }


    
    
    private Vector3 GetFloorReviewPlateSize(string category)
    {
        // 라벨 박스가 도면을 가리지 않도록 축소
        if (category == "building") return new Vector3(3.8f, 0.035f, 2.1f);
        if (category == "parking") return new Vector3(5.8f, 0.035f, 2.6f);
        if (category == "pump") return new Vector3(5.4f, 0.035f, 2.4f);
        if (category == "electric") return new Vector3(5.8f, 0.035f, 2.4f);
        if (category == "heat") return new Vector3(5.0f, 0.035f, 2.2f);
        if (category == "pit") return new Vector3(4.4f, 0.035f, 2.1f);
        return new Vector3(4.0f, 0.035f, 2.0f);
    }



    private void CreateFloorReviewOutline(Transform parent, Color color, Vector3 size)
    {
        Material mat = CreateOpaqueMat(color);

        float w = size.x;
        float h = size.z;
        float y = 0.055f;
        float t = 0.08f;

        CreateOutlineCube(parent, "외곽선_TOP", new Vector3(0, y, h * 0.5f), new Vector3(w, t, t), mat);
        CreateOutlineCube(parent, "외곽선_BOTTOM", new Vector3(0, y, -h * 0.5f), new Vector3(w, t, t), mat);
        CreateOutlineCube(parent, "외곽선_LEFT", new Vector3(-w * 0.5f, y, 0), new Vector3(t, t, h), mat);
        CreateOutlineCube(parent, "외곽선_RIGHT", new Vector3(w * 0.5f, y, 0), new Vector3(t, t, h), mat);
    }

    private void CreateOutlineCube(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localScale = localScale;
        go.GetComponent<Renderer>().sharedMaterial = mat;
    }



    
    
    
    private bool TryGetFloorReviewTargetBounds(out Bounds bounds)
    {
        // 사용자가 보는 파란 바닥 기준으로 라벨을 맞춘다.
        string[] candidates = new string[]
        {
            "EXCAVATION_BOTTOM",
            "FINAL_BOTTOM_STEP",
            "BOTTOM_ZONE_LINE",
            "BOTTOM_EL_ZONE"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[FLOOR_REVIEW_INFO] 기준 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(210f, 2f, 260f));
        Debug.LogWarning("[FLOOR_REVIEW_INFO] 파란 바닥 Bounds를 못 찾아 fallback Bounds 사용");
        return true;
    }




    private GameObject FindGameObjectIncludingInactive(string objectName)
    {
        GameObject[] all = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in all)
        {
            if (go == null)
                continue;

            if (go.name == objectName)
                return go;
        }

        return null;
    }

    private bool TryCalculateBounds(GameObject root, out Bounds bounds)
    {
        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
        bool has = false;
        bounds = new Bounds(root.transform.position, Vector3.zero);

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            if (!has)
            {
                bounds = r.bounds;
                has = true;
            }
            else
            {
                bounds.Encapsulate(r.bounds);
            }
        }

        return has;
    }

    
    
    
    private Vector3 MapFloorReviewDxfToWorld(
        float dxfX,
        float dxfY,
        float minX,
        float maxX,
        float minY,
        float maxY,
        Bounds targetBounds)
    {
        float nx = Mathf.InverseLerp(minX, maxX, dxfX);
        float nz = Mathf.InverseLerp(minY, maxY, dxfY);

        // 현재 캡처 기준 전체 배열은 맞으므로 반전하지 않는다.
        // 필요 시 아래 둘 중 하나만 활성화.
        // nx = 1f - nx;
        // nz = 1f - nz;

        // 파란 바닥 내부에 정확히 들어오도록 내부 여백 적용
        float marginX = targetBounds.size.x * 0.12f;
        float marginZ = targetBounds.size.z * 0.12f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        // 바닥 위로 띄우기
        float y = targetBounds.max.y + 8.00f;

        return new Vector3(x, y, z);
    }






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

        string json = LoadReviewJsonText("post_pile_number_points_v1.json");
        if (string.IsNullOrEmpty(json))
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON 없음(Resources): post_pile_number_points_v1.json");
            return;
        }

        PostPileNumberPointRoot root = JsonUtility.FromJson<PostPileNumberPointRoot>(json);

        if (root == null || root.points == null || root.points.Length == 0)
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON에 point 없음");
            return;
        }

        Bounds targetBounds;
        if (!TryGetPostPileNumberTargetBounds(out targetBounds))
        {
            targetBounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
            Debug.LogWarning("[POST_PILE_NUMBER] 기준 Bounds fallback 사용");
        }

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minY = float.MaxValue;
        float maxY = float.MinValue;

        foreach (var p in root.points)
        {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.y > maxY) maxY = p.y;
        }

        // PF 좌표 전체 범위에 약간 여유
        float padX = (maxX - minX) * 0.01f;
        float padY = (maxY - minY) * 0.01f;
        minX -= padX;
        maxX += padX;
        minY -= padY;
        maxY += padY;

        postPileNumberGroup = new GameObject("POST_PILE_NUMBER_MARKER");
        postPileNumberGroup.transform.SetParent(this.transform, false);

        Material discMat = CreatePostPileNumberDiscMaterial();
        Material outlineMat = CreatePostPileNumberOutlineMaterial();

        Font font = KoreanFontProvider.Get();

        int created = 0;

        foreach (var p in root.points)
        {
            if (p.no < 1 || p.no > 492)
                continue;

            // 전체 492개는 너무 촘촘하므로 우선 주요번호만 표시
            // P001, P010, P020 ... P490, P492
            bool showMajor =
                p.no == 1 ||
                p.no == 492 ||
                p.no % 10 == 0;

            if (!showMajor)
                continue;

            Vector3 pos = MapPostPilePointToWorld(p.x, p.y, minX, maxX, minY, maxY, targetBounds);
            CreatePostPileNumberMarker(postPileNumberGroup.transform, p.no, pos, discMat, outlineMat, font);
            created++;
        }

        postPileNumberGroup.SetActive(false);

        Debug.Log("[POST_PILE_NUMBER] JSON point count: " + root.points.Length);
        Debug.Log("[POST_PILE_NUMBER] 주요 포스트파일 번호 생성: " + created);
        Debug.Log("[POST_PILE_NUMBER] targetBounds center=" + targetBounds.center + " size=" + targetBounds.size);
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
        root.transform.rotation = Quaternion.identity;

        Material whiteMat = CreatePostPileNumberDiscMaterial();
        Material blackMat = CreatePostPileNumberOutlineMaterial();

        // 흰색 원형판
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "PILE_NO_DISC_" + no.ToString("000");
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = new Vector3(0f, 0f, 0f);
        disc.transform.localScale = new Vector3(1.25f, 0.055f, 1.25f);

        Renderer dr = disc.GetComponent<Renderer>();
        if (dr != null)
        {
            dr.sharedMaterial = whiteMat;
            dr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            dr.receiveShadows = false;
        }

        Collider dc = disc.GetComponent<Collider>();
        if (dc != null) DestroyImmediate(dc);

        // 검정 외곽 원
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "PILE_NO_OUTLINE_" + no.ToString("000");
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = new Vector3(0f, -0.08f, 0f);
        outline.transform.localScale = new Vector3(1.42f, 0.04f, 1.42f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = blackMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 번호 텍스트
        GameObject txtObj = new GameObject("PILE_NO_TEXT_" + no.ToString("000"));
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 2.20f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = "P" + no.ToString("000");
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 320;
        tm.characterSize = 0.095f;
        tm.color = Color.black;
        tm.richText = false;
        tm.fontStyle = FontStyle.Bold;

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = txtObj.GetComponent<MeshRenderer>();
            if (mr != null && font.material != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.black;
                textMat.renderQueue = 8000;
                mr.sharedMaterial = textMat;
            }
        }

        Font useFont = font;
        if (useFont == null)
            useFont = KoreanFontProvider.Get();

        if (useFont != null)
        {
            tm.font = useFont;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(useFont.material);
                textMat.color = Color.black;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }















    
    
    
    
    
    private bool TryGetPostPileNumberTargetBounds(out Bounds bounds)
    {
        // 번호는 바닥이 아니라 캡빔/PF/CIP 상단 외곽에 맞춰야 한다.
        // EXCAVATION_BOTTOM은 안쪽 바닥 기준이라 사용 우선순위를 낮춘다.
        string[] candidates = new string[]
        {
            "CIP",
            "PF",
            "PF_HPILE",
            "WALE_SPEC_REVIEW",
            "Wangsuk_CAD_3D_ROOT",
            "EXCAVATION_BOTTOM"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[POST_PILE_NUMBER] 기준 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(new Vector3(65.45f, -7.30f, 202.50f), new Vector3(241.20f, 26.10f, 304.15f));
        Debug.LogWarning("[POST_PILE_NUMBER] 기준 Bounds fallback 사용");
        return true;
    }






    
    
    
    
    
    
    
    
    private Vector3 MapPostPilePointToWorld(
        float srcX,
        float srcY,
        float minX,
        float maxX,
        float minY,
        float maxY,
        Bounds targetBounds)
    {
        // PF points[] 평균좌표는 DXF 원좌표이므로 targetBounds에 매핑한다.
        float nx = Mathf.InverseLerp(minX, maxX, srcX);
        float nz = Mathf.InverseLerp(minY, maxY, srcY);

        // 마진을 거의 두지 않아 캡빔 외곽에 가깝게 붙인다.
        float marginX = targetBounds.size.x * 0.004f;
        float marginZ = targetBounds.size.z * 0.004f;

        float x = Mathf.Lerp(targetBounds.min.x + marginX, targetBounds.max.x - marginX, nx);
        float z = Mathf.Lerp(targetBounds.min.z + marginZ, targetBounds.max.z - marginZ, nz);

        Vector3 c = targetBounds.center;

        // 이전보다 바깥쪽으로 확장.
        // 번호가 안쪽에 생성되었으므로 1보다 크게 잡는다.
        float expand = 1.08f;
        x = c.x + (x - c.x) * expand;
        z = c.z + (z - c.z) * expand;

        // 캡빔 상단보다 확실히 위
        float y = targetBounds.max.y + 2.20f;

        return new Vector3(x, y, z);
    }












    
    private Material CreatePostPileNumberDigitMaterial()
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 5000;
        return mat;
    }


    private void CreatePileNumberDigits3D(Transform parent, string numberText, Material mat)
    {
        int len = numberText.Length;

        float digitWidth = 0.30f;
        float digitHeight = 0.50f;
        float gap = 0.16f;

        float totalWidth = len * digitWidth + (len - 1) * gap;
        float startX = -totalWidth * 0.5f + digitWidth * 0.5f;

        for (int i = 0; i < len; i++)
        {
            char ch = numberText[i];
            float x = startX + i * (digitWidth + gap);
            CreateSevenSegmentDigit(parent, ch, new Vector3(x, 0.145f, 0f), digitWidth, digitHeight, mat);
        }
    }

    private void CreateSevenSegmentDigit(Transform parent, char ch, Vector3 center, float width, float height, Material mat)
    {
        // 7세그먼트 위치
        //   A
        // F   B
        //   G
        // E   C
        //   D

        bool A = false, B = false, C = false, D = false, E = false, F = false, G = false;

        switch (ch)
        {
            case '0': A = B = C = D = E = F = true; break;
            case '1': B = C = true; break;
            case '2': A = B = G = E = D = true; break;
            case '3': A = B = C = D = G = true; break;
            case '4': F = G = B = C = true; break;
            case '5': A = F = G = C = D = true; break;
            case '6': A = F = E = D = C = G = true; break;
            case '7': A = B = C = true; break;
            case '8': A = B = C = D = E = F = G = true; break;
            case '9': A = B = C = D = F = G = true; break;
            default: return;
        }

        float t = 0.055f;
        float y = center.y;
        float zTop = center.z + height * 0.42f;
        float zMid = center.z;
        float zBot = center.z - height * 0.42f;
        float xLeft = center.x - width * 0.42f;
        float xRight = center.x + width * 0.42f;

        float hLen = width * 0.72f;
        float vLen = height * 0.36f;

        if (A) CreateDigitBar(parent, "A", new Vector3(center.x, y, zTop), new Vector3(hLen, t, t), mat);
        if (G) CreateDigitBar(parent, "G", new Vector3(center.x, y, zMid), new Vector3(hLen, t, t), mat);
        if (D) CreateDigitBar(parent, "D", new Vector3(center.x, y, zBot), new Vector3(hLen, t, t), mat);

        if (B) CreateDigitBar(parent, "B", new Vector3(xRight, y, center.z + height * 0.21f), new Vector3(t, t, vLen), mat);
        if (C) CreateDigitBar(parent, "C", new Vector3(xRight, y, center.z - height * 0.21f), new Vector3(t, t, vLen), mat);
        if (F) CreateDigitBar(parent, "F", new Vector3(xLeft, y, center.z + height * 0.21f), new Vector3(t, t, vLen), mat);
        if (E) CreateDigitBar(parent, "E", new Vector3(xLeft, y, center.z - height * 0.21f), new Vector3(t, t, vLen), mat);
    }

    private void CreateDigitBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
        bar.name = "DIGIT_BAR_" + name;
        bar.transform.SetParent(parent, false);
        bar.transform.localPosition = localPos;
        bar.transform.localScale = localScale;

        Renderer r = bar.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider col = bar.GetComponent<Collider>();
        if (col != null) DestroyImmediate(col);
    }






    private void CreatePostPileNumberTextMesh(Transform parent, string textValue, Vector3 localPos, Quaternion localRot, Font font)
    {
        GameObject txtObj = new GameObject("번호텍스트_" + textValue);
        txtObj.transform.SetParent(parent, false);
        txtObj.transform.localPosition = localPos;
        txtObj.transform.localRotation = localRot;
        txtObj.transform.localScale = Vector3.one;

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = textValue;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 120;
        tm.characterSize = 0.115f;
        tm.color = Color.black;
        tm.richText = false;

        Font useFont = font;
        if (useFont == null)
            useFont = KoreanFontProvider.Get();

        if (useFont != null)
        {
            tm.font = useFont;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(useFont.material);
                textMat.color = Color.black;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }


    private Material CreatePostPileNumberBoardMaterial()
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(1f, 1f, 0.65f, 0.96f);
        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 1);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3500;
        return mat;
    }

    private void CreateNumberBoardBorder(Transform parent, Material mat)
    {
        float w = 1.22f;
        float h = 0.82f;
        float t = 0.045f;
        float z = -0.07f;

        CreateBoardBar(parent, "번호판_BORDER_TOP", new Vector3(0f, h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBoardBar(parent, "번호판_BORDER_BOTTOM", new Vector3(0f, -h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBoardBar(parent, "번호판_BORDER_LEFT", new Vector3(-w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
        CreateBoardBar(parent, "번호판_BORDER_RIGHT", new Vector3(w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
    }

    private void CreateBoardBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localScale = localScale;

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




    private void CreateFlatNumberPlateBorder(Transform parent, Material mat)
    {
        float w = 1.34f;
        float h = 0.94f;
        float t = 0.055f;
        float y = 0.075f;

        CreateFlatDigitBar(parent, "번호판_TOP", new Vector3(0f, y, h * 0.5f), new Vector3(w, 0.06f, t), mat);
        CreateFlatDigitBar(parent, "번호판_BOTTOM", new Vector3(0f, y, -h * 0.5f), new Vector3(w, 0.06f, t), mat);
        CreateFlatDigitBar(parent, "번호판_LEFT", new Vector3(-w * 0.5f, y, 0f), new Vector3(t, 0.06f, h), mat);
        CreateFlatDigitBar(parent, "번호판_RIGHT", new Vector3(w * 0.5f, y, 0f), new Vector3(t, 0.06f, h), mat);
    }

    


    private void CreatePileNumberDigitsFlat3D(Transform parent, string numberText, Material mat)
    {
        int len = numberText.Length;

        float digitWidth = 0.28f;
        float digitHeight = 0.52f;
        float gap = 0.07f;

        float totalWidth = len * digitWidth + (len - 1) * gap;
        float startX = -totalWidth * 0.5f + digitWidth * 0.5f;

        for (int i = 0; i < len; i++)
        {
            char ch = numberText[i];
            float x = startX + i * (digitWidth + gap);
            CreateSevenSegmentDigitFlat(parent, ch, new Vector3(x, 0.18f, 0f), digitWidth, digitHeight, mat);
        }
    }

    private void CreateSevenSegmentDigitFlat(Transform parent, char ch, Vector3 center, float width, float height, Material mat)
    {
        bool A = false, B = false, C = false, D = false, E = false, F = false, G = false;

        switch (ch)
        {
            case '0': A = B = C = D = E = F = true; break;
            case '1': B = C = true; break;
            case '2': A = B = G = E = D = true; break;
            case '3': A = B = C = D = G = true; break;
            case '4': F = G = B = C = true; break;
            case '5': A = F = G = C = D = true; break;
            case '6': A = F = E = D = C = G = true; break;
            case '7': A = B = C = true; break;
            case '8': A = B = C = D = E = F = G = true; break;
            case '9': A = B = C = D = F = G = true; break;
            default: return;
        }

        float t = 0.055f;
        float y = center.y;

        float zTop = center.z + height * 0.42f;
        float zMid = center.z;
        float zBot = center.z - height * 0.42f;

        float xLeft = center.x - width * 0.42f;
        float xRight = center.x + width * 0.42f;

        float hLen = width * 0.72f;
        float vLen = height * 0.36f;

        if (A) CreateFlatDigitBar(parent, "DIGIT_A", new Vector3(center.x, y, zTop), new Vector3(hLen, 0.075f, t), mat);
        if (G) CreateFlatDigitBar(parent, "DIGIT_G", new Vector3(center.x, y, zMid), new Vector3(hLen, 0.075f, t), mat);
        if (D) CreateFlatDigitBar(parent, "DIGIT_D", new Vector3(center.x, y, zBot), new Vector3(hLen, 0.075f, t), mat);

        if (B) CreateFlatDigitBar(parent, "DIGIT_B", new Vector3(xRight, y, center.z + height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
        if (C) CreateFlatDigitBar(parent, "DIGIT_C", new Vector3(xRight, y, center.z - height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
        if (F) CreateFlatDigitBar(parent, "DIGIT_F", new Vector3(xLeft, y, center.z + height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
        if (E) CreateFlatDigitBar(parent, "DIGIT_E", new Vector3(xLeft, y, center.z - height * 0.21f), new Vector3(t, 0.075f, vLen), mat);
    }

    private void CreateFlatDigitBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
        bar.name = name;
        bar.transform.SetParent(parent, false);
        bar.transform.localPosition = localPos;
        bar.transform.localScale = localScale;

        Renderer r = bar.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = bar.GetComponent<Collider>();
        if (c != null) DestroyImmediate(c);
    }




    private void CreatePileNumberDigitsBig3D(Transform parent, string numberText, Material mat)
    {
        int len = numberText.Length;

        float digitWidth = 0.72f;
        float digitHeight = 1.35f;
        float gap = 0.16f;

        if (len == 1)
        {
            digitWidth = 0.46f;
            digitHeight = 0.82f;
        }
        else if (len == 2)
        {
            digitWidth = 0.40f;
            digitHeight = 0.76f;
        }

        float totalWidth = len * digitWidth + (len - 1) * gap;
        float startX = -totalWidth * 0.5f + digitWidth * 0.5f;

        for (int i = 0; i < len; i++)
        {
            char ch = numberText[i];
            float x = startX + i * (digitWidth + gap);
            CreateSevenSegmentDigitBig(parent, ch, new Vector3(x, 0.28f, 0f), digitWidth, digitHeight, mat);
        }
    }

    private void CreateSevenSegmentDigitBig(Transform parent, char ch, Vector3 center, float width, float height, Material mat)
    {
        bool A = false, B = false, C = false, D = false, E = false, F = false, G = false;

        switch (ch)
        {
            case '0': A = B = C = D = E = F = true; break;
            case '1': B = C = true; break;
            case '2': A = B = G = E = D = true; break;
            case '3': A = B = C = D = G = true; break;
            case '4': F = G = B = C = true; break;
            case '5': A = F = G = C = D = true; break;
            case '6': A = F = E = D = C = G = true; break;
            case '7': A = B = C = true; break;
            case '8': A = B = C = D = E = F = G = true; break;
            case '9': A = B = C = D = F = G = true; break;
            default: return;
        }

        float t = 0.18f;
        float y = center.y;

        float zTop = center.z + height * 0.42f;
        float zMid = center.z;
        float zBot = center.z - height * 0.42f;

        float xLeft = center.x - width * 0.43f;
        float xRight = center.x + width * 0.43f;

        float hLen = width * 0.76f;
        float vLen = height * 0.38f;

        if (A) CreatePileDigitCube(parent, "A", new Vector3(center.x, y, zTop), new Vector3(hLen, 0.22f, t), mat);
        if (G) CreatePileDigitCube(parent, "G", new Vector3(center.x, y, zMid), new Vector3(hLen, 0.22f, t), mat);
        if (D) CreatePileDigitCube(parent, "D", new Vector3(center.x, y, zBot), new Vector3(hLen, 0.22f, t), mat);

        if (B) CreatePileDigitCube(parent, "B", new Vector3(xRight, y, center.z + height * 0.21f), new Vector3(t, 0.22f, vLen), mat);
        if (C) CreatePileDigitCube(parent, "C", new Vector3(xRight, y, center.z - height * 0.21f), new Vector3(t, 0.22f, vLen), mat);
        if (F) CreatePileDigitCube(parent, "F", new Vector3(xLeft, y, center.z + height * 0.21f), new Vector3(t, 0.22f, vLen), mat);
        if (E) CreatePileDigitCube(parent, "E", new Vector3(xLeft, y, center.z - height * 0.21f), new Vector3(t, 0.22f, vLen), mat);
    }

    private void CreatePileDigitCube(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "PILE_DIGIT_" + name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localScale = localScale;

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


    


    private Material CreatePostPileNumberBillboardBoardMaterial()
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(1f, 0.92f, 0.15f, 1f);
        mat.renderQueue = 4500;
        return mat;
    }

    private void CreateBillboardBoardBorder(Transform parent, Material mat)
    {
        float w = 1.18f;
        float h = 0.70f;
        float t = 0.045f;
        float z = -0.070f;

        CreateBillboardBorderBar(parent, "번호판_TOP", new Vector3(0f, h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBillboardBorderBar(parent, "번호판_BOTTOM", new Vector3(0f, -h * 0.5f, z), new Vector3(w, t, t), mat);
        CreateBillboardBorderBar(parent, "번호판_LEFT", new Vector3(-w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
        CreateBillboardBorderBar(parent, "번호판_RIGHT", new Vector3(w * 0.5f, 0f, z), new Vector3(t, h, t), mat);
    }

    private void CreateBillboardBorderBar(Transform parent, string name, Vector3 localPos, Vector3 localScale, Material mat)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localScale = localScale;

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

    private void CreatePostPileBillboardText(Transform parent, string value, Vector3 localPos, Quaternion localRot, Font font)
    {
        GameObject txtObj = new GameObject("번호텍스트_" + value);
        txtObj.transform.SetParent(parent, false);
        txtObj.transform.localPosition = localPos;
        txtObj.transform.localRotation = localRot;

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = value;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 160;
        tm.characterSize = 0.105f;
        tm.color = Color.black;
        tm.richText = false;

        Font useFont = font;
        if (useFont == null)
            useFont = KoreanFontProvider.Get();

        if (useFont != null)
        {
            tm.font = useFont;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(useFont.material);
                textMat.color = Color.black;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }


    


    private bool TryGetPileMajorCalloutBounds(out Bounds bounds)
    {
        // 도면/바닥 전체가 아니라 흙막이 상단 외곽을 기준으로 잡는다.
        string[] candidates = new string[]
        {
            "CIP",
            "PF",
            "PF_HPILE",
            "Wangsuk_CAD_3D_ROOT",
            "EXCAVATION_BOTTOM"
        };

        foreach (string name in candidates)
        {
            GameObject go = FindGameObjectIncludingInactive(name);
            if (go == null)
                continue;

            if (TryCalculateBounds(go, out bounds))
            {
                Debug.Log("[POST_PILE_NUMBER] 주요번호 Bounds 그룹: " + name + " center=" + bounds.center + " size=" + bounds.size);
                return true;
            }
        }

        bounds = new Bounds(Vector3.zero, Vector3.one);
        return false;
    }

    private void CreatePileMajorCallout(Transform parent, string label, float nx, float nz, Bounds b, float y)
    {
        float marginX = b.size.x * 0.04f;
        float marginZ = b.size.z * 0.04f;

        float x = Mathf.Lerp(b.min.x + marginX, b.max.x - marginX, nx);
        float z = Mathf.Lerp(b.min.z + marginZ, b.max.z - marginZ, nz);

        GameObject root = new GameObject("PILE_CALLOUT_" + label);
        root.transform.SetParent(parent, false);
        root.transform.position = new Vector3(x, y, z);

        Material whiteMat = CreatePostPileNumberDiscMaterial();
        Material blackMat = CreatePostPileNumberOutlineMaterial();

        // 원형 배경
        GameObject disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        disc.name = "CALLOUT_DISC_" + label;
        disc.transform.SetParent(root.transform, false);
        disc.transform.localPosition = new Vector3(0f, 0f, 0f);
        disc.transform.localScale = new Vector3(2.2f, 0.06f, 2.2f);

        Renderer dr = disc.GetComponent<Renderer>();
        if (dr != null)
        {
            dr.sharedMaterial = whiteMat;
            dr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            dr.receiveShadows = false;
        }

        Collider dc = disc.GetComponent<Collider>();
        if (dc != null) DestroyImmediate(dc);

        // 검은 외곽
        GameObject outline = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        outline.name = "CALLOUT_OUTLINE_" + label;
        outline.transform.SetParent(root.transform, false);
        outline.transform.localPosition = new Vector3(0f, -0.08f, 0f);
        outline.transform.localScale = new Vector3(2.45f, 0.04f, 2.45f);

        Renderer or = outline.GetComponent<Renderer>();
        if (or != null)
        {
            or.sharedMaterial = blackMat;
            or.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            or.receiveShadows = false;
        }

        Collider oc = outline.GetComponent<Collider>();
        if (oc != null) DestroyImmediate(oc);

        // 텍스트
        GameObject txtObj = new GameObject("CALLOUT_TEXT_" + label);
        txtObj.transform.SetParent(root.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.18f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = label;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 120;
        tm.characterSize = 0.095f;
        tm.color = Color.black;
        tm.richText = false;

        Font font = KoreanFontProvider.Get();
        if (font != null)
        {
            tm.font = font;
            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.black;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }

    private Material CreatePostPileNumberDiscMaterial()
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(1f, 1f, 1f, 1f);
        mat.renderQueue = 4500;
        return mat;
    }



    
    
    private Material CreatePostPileNumberOutlineMaterial()
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(0f, 0f, 0f, 1f);
        mat.renderQueue = 4400;
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




    private GameObject soilFillVolumeGroup;

    
    
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

        float innerScaleX = 0.78f;
        float innerScaleZ = 0.78f;

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

                Color sideColor = new Color(color.r, color.g, color.b, 0.42f);
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
            return new Color(lv.color[0], lv.color[1], lv.color[2], Mathf.Min(lv.color[3], 0.075f));

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


    private void CreateSoilFillLayer(string layerName, float cx, float cz, float sx, float sz, float topY, float bottomY, Color color)
    {
        float h = Mathf.Abs(topY - bottomY);
        float cy = (topY + bottomY) * 0.5f;

        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "SOIL_FILL_" + layerName;
        go.transform.SetParent(soilFillVolumeGroup.transform, false);
        go.transform.position = new Vector3(cx, cy, cz);
        go.transform.localScale = new Vector3(sx, h, sz);

        Renderer r = go.GetComponent<Renderer>();
        if (r != null)
        {
            r.sharedMaterial = CreateSoilFillTransparentMaterial(color);
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = go.GetComponent<Collider>();
        if (c != null) DestroyImmediate(c);

        // 레벨명 라벨
        CreateSoilFillLayerLabel(layerName, cx, topY + 0.15f, cz, color);
    }

    private void CreateSoilFillLayerLabel(string label, float x, float y, float z, Color color)
    {
        GameObject labelRoot = new GameObject("SOIL_FILL_LABEL_" + label);
        labelRoot.transform.SetParent(soilFillVolumeGroup.transform, false);
        labelRoot.transform.position = new Vector3(x, y, z);

        GameObject bg = GameObject.CreatePrimitive(PrimitiveType.Cube);
        bg.name = "LABEL_BG_" + label;
        bg.transform.SetParent(labelRoot.transform, false);
        bg.transform.localPosition = Vector3.zero;
        bg.transform.localScale = new Vector3(8.0f, 0.06f, 2.2f);

        Color bgColor = new Color(color.r, color.g, color.b, 0.72f);

        Renderer br = bg.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = CreateSoilFillTransparentMaterial(bgColor);
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = bg.GetComponent<Collider>();
        if (bc != null) DestroyImmediate(bc);

        GameObject txtObj = new GameObject("LABEL_TEXT_" + label);
        txtObj.transform.SetParent(labelRoot.transform, false);
        txtObj.transform.localPosition = new Vector3(0f, 0.12f, 0f);
        txtObj.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = txtObj.AddComponent<TextMesh>();
        tm.text = label;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.fontSize = 100;
        tm.characterSize = 0.075f;
        tm.color = Color.white;
        tm.richText = false;

        Font font = KoreanFontProvider.Get();
        if (font != null)
        {
            tm.font = font;

            Renderer tr = txtObj.GetComponent<Renderer>();
            if (tr != null)
            {
                Material textMat = new Material(font.material);
                textMat.color = Color.white;
                textMat.renderQueue = 5000;
                tr.sharedMaterial = textMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }
        }
    }

    private Material CreateSoilFillTransparentMaterial(Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = color;

        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);

        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");

        mat.renderQueue = 3100;
        return mat;
    }

    public void SetSoilFillVolume(bool active)
    {
        if (soilFillVolumeGroup == null)
            BuildSoilFillVolume();

        if (soilFillVolumeGroup != null)
        {
            soilFillVolumeGroup.SetActive(active);
            Debug.Log("[SOIL_FILL_VOLUME] 표시 상태: " + active);
        }
    }

    public void ToggleSoilFillVolume()
    {
        if (soilFillVolumeGroup == null)
            BuildSoilFillVolume();

        if (soilFillVolumeGroup != null)
            soilFillVolumeGroup.SetActive(!soilFillVolumeGroup.activeSelf);
    }



    public void HideBoxSoilFillVolume()
    {
        GameObject oldBox = GameObject.Find("SOIL_FILL_VOLUME");
        if (oldBox != null)
        {
            oldBox.SetActive(false);
            Debug.Log("[SOIL_FILL_VOLUME] 박스형 흙채움 숨김 처리");
        }
    }

    public void ToggleSoilRockLayerClean()
    {
        // 기존 박스형 흙채움은 사용하지 않음
        GameObject box = FindGameObjectIncludingInactive("SOIL_FILL_VOLUME");
        if (box != null)
        {
            box.SetActive(false);
            Debug.Log("[SOIL_FILL_VOLUME] 박스형 흙채움 숨김");
        }

        GameObject layer = FindGameObjectIncludingInactive("SOIL_ROCK_LAYER");
        GameObject text = FindGameObjectIncludingInactive("SOIL_ROCK_TEXT");

        // 혹시 아직 생성 전이면 PF 기준 지층밴드 생성
        if (layer == null)
        {
            BuildSoilRockBandsAndLabels("c605_pf_hpile.json");
// 토공바닥 0m 기준 / 최상단 포스트 캡까지 1m 간격 높이 기준자
            layer = FindGameObjectIncludingInactive("SOIL_ROCK_LAYER");
            text = FindGameObjectIncludingInactive("SOIL_ROCK_TEXT");
        }

        if (layer == null)
        {
            Debug.LogWarning("[SOIL_ROCK_LAYER] 그룹을 찾지 못했습니다.");
            return;
        }

        bool next = !layer.activeSelf;

        layer.SetActive(next);

        if (text != null)
            text.SetActive(next);

        Debug.Log("[SOIL_ROCK_LAYER] PF라인 지층밴드 표시 상태: " + next);
    }
    private Color ParseHtmlColor(string html, Color fallback)
    {
        if (string.IsNullOrEmpty(html))
            return fallback;

        Color c;
        if (ColorUtility.TryParseHtmlString(html, out c))
            return c;

        return fallback;
    }

    private Material CreateTransparentMat(Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = color;
        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;
        return mat;
    }

    private Material CreateOpaqueMat(Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = color;
        return mat;
    }

    
    public void SetFloorReviewInfoOverlay(bool active)
    {
        if (floorReviewInfoGroup == null)
        {
            BuildFloorReviewInfoOverlay();
        }

        if (floorReviewInfoGroup != null)
        {
            floorReviewInfoGroup.SetActive(active);
            Debug.Log("[FLOOR_REVIEW_INFO] 표시 상태: " + active);
        }
        else
        {
            Debug.LogWarning("[FLOOR_REVIEW_INFO] 그룹 생성 실패");
        }
    }
public void ToggleFloorReviewInfoOverlay()
    {
        if (floorReviewInfoGroup == null)
            BuildFloorReviewInfoOverlay();

        if (floorReviewInfoGroup == null)
            return;

        floorReviewInfoGroup.SetActive(!floorReviewInfoGroup.activeSelf);
    }
private void Awake()
    {
        if (registry == null)
            registry = GetComponent<ModelGroupRegistry>();

        if (registry == null)
            registry = gameObject.AddComponent<ModelGroupRegistry>();

        registry.Init();
        CreateDefaultMaterials();
    }

    private Material MakeOpaqueMat(string name, Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.name = name;
        mat.color = color;
        return mat;
    }

    private Material MakeTransparentMat(string name, Color color, float alpha)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.name = name;

        Color c = color;
        c.a = alpha;
        mat.color = c;

        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;

        return mat;
    }

    private void CreateDefaultMaterials()
    {
        pfLineMaterial = MakeOpaqueMat("C605_PF_Line_Red", new Color(1.0f, 0.05f, 0.02f));
        pfWallMaterial = MakeTransparentMat("C605_PF_Wall_Red_Transparent", new Color(1.0f, 0.05f, 0.02f), 0.38f);

        cipMaterial = MakeTransparentMat("C605_CIP_Cyan_Transparent", new Color(0.0f, 0.75f, 1.0f), 0.42f);
        cipTopMaterial = MakeOpaqueMat("C605_CIP_Top_Cyan", new Color(0.0f, 0.95f, 1.0f));

        // 띠장: 도면 검토용으로 노랑/주황
        waleMaterial = MakeOpaqueMat("C605_WALE_2H_Orange", new Color(1.0f, 0.65f, 0.0f));
    }

    public void BuildAll()
    {
        ClearAll();

        registry = GetComponent<ModelGroupRegistry>();
        if (registry == null)
            registry = gameObject.AddComponent<ModelGroupRegistry>();

        registry.root = null;
        registry.Init();

        BuildPFPolyline("c605_pf_hpile.json", "PF_HPILE");
        BuildCIPCylinders("c605_cip.json", "CIP");

        // C-612~C-619 굴착계획 전개도 기준:
        // 구간별 2단 / 3단 띠장 적용
        BuildWaleLevelsByPfCenters("c605_pf_hpile.json", "WALE");

        // C-605 평면도 STRUT / BEAM-BRACING 레이어 기준
        // C-612~C-619 전개도 분석 결과 STRUT는 WALE 1단 높이군과 일치.
        // 따라서 현재는 STRUT_L1 / CORNER_STRUT_L1 1단만 생성한다.
        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");

        // C-616~C-618 전개도 검토 기준 4단 띠장 강제 보강
        BuildForceWaleLevel4FromPfCenters("c605_pf_hpile.json");

        BuildWaleSpecReviewFromPfCenters("c605_pf_hpile.json");

        // C-605 평면도 Anchor_1단 / ANCHOR 레이어 기준
        // 길이 1000 이상 본체만 ANCHOR_L1로 생성
        BuildAnchorSpecReviewFromPfCenters("c605_pf_hpile.json", "ANCHOR_L1");

        // C-605 PF/H-PILE 중심선 기준 굴착면/바닥/바닥 글씨 생성
        // 실제 토질/암질 층 및 정확한 EL은 굴착계획 전개도/단면도 검토 후 추가 보정
        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");

        // C-610~C-619 도면 문자 기준 지층 표현
        // 확인 지층: 매립층 / 퇴적층 / 풍화토 / 풍화암
        BuildSoilRockBandsAndLabels("c605_pf_hpile.json");

        // C-612~C-619 굴착계획 전개도 기준 구간별 시공하한선 EL 표시
        BuildSectionBottomElLabels("c605_pf_hpile.json");

        // 도면 PILE NO 기준 바닥 EL 구간 경계선 표시
        BuildBottomZoneLines("c605_pf_hpile.json");

        // 토공바닥 0m 기준 / 최상단 포스트 캡까지 1m 간격 높이 기준자
        Debug.Log("[ELEVATION_RULER] 생성 호출 시작");
        BuildElevationRulerFromModelBounds();
        Debug.Log("[ELEVATION_RULER] 생성 호출 완료");

        // BOTTOM_EL_ZONE 큰 면 방식은 모델을 복잡하게 만들어 사용 중지
        // BuildBottomElZones("c605_pf_hpile.json");

        // C-605 굴착계획 평면도 바닥 도면 오버레이
        BuildC605PlanOverlay("c605_pf_hpile.json");

        // C-605 바닥 동자리/건물선 벡터 오버레이
        BuildDongjariVectorOverlay("c605_floor_dongjari_overlay.json");

        // 동자리/건물선 기준 최종 바닥 단차 후보 표시
        BuildFinalBottomStepFromDongjari("c605_floor_dongjari_overlay.json");

        // C-612~C-619 전개도 기준 PILE NO 구간 경계/라벨 표시
        BuildPileSectionMarkers("c605_pf_hpile.json");

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root != null)
        {
            WangsukSceneNormalizer.NormalizeRootToOrigin(root, 3f);
        }

        Debug.Log("C-605 PF/CIP + WALE 단수 반영 모델 생성 완료");
    }

    public void ClearAll()
    {
        GameObject oldRoot = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (oldRoot != null)
            DestroyImmediate(oldRoot);
    }

    private void BuildPFPolyline(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
            return;

        GameObject group = registry.GetGroup(groupKey);
        if (group == null)
            return;

        int lineCreated = 0;
        int wallCreated = 0;

        foreach (var e in data.entities)
        {
            if (!e.has_points || e.points == null || e.points.Count < 2)
                continue;

            List<Vector3> pts = ConvertEntityPoints(e, 0.2f);

            GameObject lineObj = new GameObject("C605_PF_TOP_LINE_" + lineCreated);
            lineObj.transform.SetParent(group.transform, false);

            LineRenderer lr = lineObj.AddComponent<LineRenderer>();
            lr.useWorldSpace = false;
            SetLineRendererPoints(lr, pts, e.closed);

            lr.startWidth = pfLineWidth;
            lr.endWidth = pfLineWidth;
            lr.numCapVertices = 6;
            lr.numCornerVertices = 6;

            if (pfLineMaterial != null)
                lr.material = pfLineMaterial;

            lineCreated++;

            int segCount = e.closed && pts.Count > 2 ? pts.Count : pts.Count - 1;

            for (int i = 0; i < segCount; i++)
            {
                Vector3 a = pts[i];
                Vector3 b = pts[(i + 1) % pts.Count];

                float len = Vector3.Distance(a, b);
                if (len < 0.05f)
                    continue;

                Vector3 mid = (a + b) * 0.5f;
                Vector3 dir = (b - a).normalized;

                GameObject wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
                wall.name = "C605_PF_WALL_SEG_" + wallCreated;
                wall.transform.SetParent(group.transform, false);

                wall.transform.position = new Vector3(mid.x, -pfWallHeight * 0.5f, mid.z);
                wall.transform.localScale = new Vector3(pfWallThickness, pfWallHeight, len);
                wall.transform.rotation = Quaternion.LookRotation(dir, Vector3.up);

                if (pfWallMaterial != null)
                    wall.GetComponent<Renderer>().material = pfWallMaterial;

                wallCreated++;
            }
        }

        Debug.Log("C605 PF 상단라인 생성: " + lineCreated);
        Debug.Log("C605 PF 벽체패널 생성: " + wallCreated);
    }

    private void BuildCIPCylinders(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
            return;

        GameObject group = registry.GetGroup(groupKey);
        if (group == null)
            return;

        int created = 0;

        foreach (var e in data.entities)
        {
            if (!e.has_center || e.center == null)
                continue;

            Vector3 pos = CadCoordinateSystem.ToUnityPoint(e.center);

            GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            obj.name = "C605_CIP_" + created;
            obj.transform.SetParent(group.transform, true);

            obj.transform.position = new Vector3(pos.x, -cipHeight / 2f, pos.z);
            obj.transform.localScale = new Vector3(cipRadius * 2f, cipHeight / 2f, cipRadius * 2f);

            if (cipMaterial != null)
                obj.GetComponent<Renderer>().material = cipMaterial;

            GameObject cap = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            cap.name = "C605_CIP_TOP_" + created;
            cap.transform.SetParent(group.transform, true);
            cap.transform.position = new Vector3(pos.x, 0.18f, pos.z);
            cap.transform.localScale = new Vector3(cipRadius * 2.15f, 0.08f, cipRadius * 2.15f);

            if (cipTopMaterial != null)
                cap.GetComponent<Renderer>().material = cipTopMaterial;

            created++;
        }

        Debug.Log("C605 CIP 원형말뚝 생성: " + created);
        Debug.Log("C605 CIP 상단캡 생성: " + created);
    }

    private void BuildWaleLevelsFromPF(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
            return;

        GameObject group = registry.GetGroup(groupKey);
        if (group == null)
        {
            Debug.LogWarning("WALE 그룹 없음: " + groupKey);
            return;
        }

        int created = 0;

        foreach (var e in data.entities)
        {
            if (!e.has_points || e.points == null || e.points.Count < 2)
                continue;

            if (buildWaleLevel1)
                created += BuildWaleBeamSegments(e, waleDepth1, "L1_0.6m");

            if (buildWaleLevel2)
                created += BuildWaleBeamSegments(e, waleDepth2, "L2_3.6m");

            if (buildWaleLevel3)
                created += BuildWaleBeamSegments(e, waleDepth3, "L3_5.6m");
        }

        Debug.Log("C605 WALE 단수 띠장 생성: " + created + " / levels="
            + (buildWaleLevel1 ? "1" : "")
            + (buildWaleLevel2 ? ",2" : "")
            + (buildWaleLevel3 ? ",3" : ""));
    }

    private int BuildWaleBeamSegments(WangsukDxfEntity e, float depthMeter, string levelName)
    {
        GameObject group = registry.GetGroup("WALE");
        if (group == null)
            return 0;

        List<Vector3> pts = ConvertEntityPoints(e, -depthMeter);

        int segCount = e.closed && pts.Count > 2 ? pts.Count : pts.Count - 1;
        int created = 0;

        for (int i = 0; i < segCount; i++)
        {
            Vector3 a = pts[i];
            Vector3 b = pts[(i + 1) % pts.Count];

            float len = Vector3.Distance(a, b);
            if (len < 0.08f)
                continue;

            Vector3 mid = (a + b) * 0.5f;
            Vector3 dir = (b - a).normalized;

            GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
            beam.name = "C605_WALE_2H_" + levelName + "_" + created;
            beam.transform.SetParent(group.transform, false);

            // Z축 방향이 부재 길이
            beam.transform.position = mid;
            beam.transform.localScale = new Vector3(waleWidth, waleHeight, len);
            beam.transform.rotation = Quaternion.LookRotation(dir, Vector3.up);

            // 벽체와 겹침을 조금 줄이기 위해 아주 살짝 안쪽/밖쪽으로 띄움
            beam.transform.position += beam.transform.right * waleOffsetFromWall;

            if (waleMaterial != null)
                beam.GetComponent<Renderer>().material = waleMaterial;

            created++;
        }

        return created;
    }

    private List<Vector3> ConvertEntityPoints(WangsukDxfEntity e, float y)
    {
        List<Vector3> pts = new List<Vector3>();

        foreach (var p in e.points)
        {
            Vector3 v = CadCoordinateSystem.ToUnityPoint(p);
            v.y = y;
            pts.Add(v);
        }

        return pts;
    }

    private void SetLineRendererPoints(LineRenderer lr, List<Vector3> pts, bool closed)
    {
        if (closed && pts.Count > 2)
        {
            lr.positionCount = pts.Count + 1;
            for (int i = 0; i < pts.Count; i++)
                lr.SetPosition(i, pts[i]);
            lr.SetPosition(pts.Count, pts[0]);
        }
        else
        {
            lr.positionCount = pts.Count;
            lr.SetPositions(pts.ToArray());
        }
    }

    private int GetWaleLevelByPfNo(int pfNo)
    {
        // 굴착계획 전개도 C-612~C-619 기준 1차 반영
        // 2단 구간: P001~P097, P365~P405, P492~P001 폐합부
        // 3단 구간: P097~P365, P405~P492

        if (pfNo >= 1 && pfNo <= 97)
            return 2;

        if (pfNo >= 98 && pfNo <= 365)
            return 3;

        if (pfNo >= 366 && pfNo <= 405)
            return 2;

        if (pfNo >= 406 && pfNo <= 492)
            return 3;

        return 2;
    }

    private void BuildWaleLevelsByPfNo(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("WALE 생성 실패: PF JSON 데이터 없음");
            return;
        }

        GameObject group = registry.GetGroup(groupKey);

        if (group == null)
        {
            GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
            if (root == null)
            {
                root = new GameObject("Wangsuk_CAD_3D_ROOT");
            }

            group = new GameObject("WALE");
            group.transform.SetParent(root.transform, false);

            Debug.LogWarning("WALE 그룹이 Registry에 없어 강제 생성했습니다.");
        }

        int created = 0;
        int pfNo = 1;
        int entityCount = 0;
        int pointEntityCount = 0;

        foreach (var e in data.entities)
        {
            entityCount++;

            if (!e.has_points || e.points == null || e.points.Count < 2)
            {
                pfNo++;
                continue;
            }

            pointEntityCount++;

            int levels = GetWaleLevelByPfNo(pfNo);

            if (levels >= 1)
                created += BuildWaleBeamSegmentsToGroup(group, e, waleDepth1, "P" + pfNo.ToString("000") + "_L1_0.6m");

            if (levels >= 2)
                created += BuildWaleBeamSegmentsToGroup(group, e, waleDepth2, "P" + pfNo.ToString("000") + "_L2_3.6m");

            if (levels >= 3)
                created += BuildWaleBeamSegmentsToGroup(group, e, waleDepth3, "P" + pfNo.ToString("000") + "_L3_5.6m");

            pfNo++;
        }

        Debug.Log("========== WALE 생성 진단 ==========");
        Debug.Log("PF JSON entityCount = " + entityCount);
        Debug.Log("PF points entityCount = " + pointEntityCount);
        Debug.Log("C605 WALE 구간별 단수 생성 = " + created);
        Debug.Log("WALE 기준: C-612~C-619 전개도 재검토 기준: P248~P428=4단 후보 반영, 기타=3단 검토");
        Debug.Log("==================================");
    }

    private int BuildWaleBeamSegmentsToGroup(GameObject group, WangsukDxfEntity e, float depthMeter, string levelName)
    {
        if (group == null)
            return 0;

        List<Vector3> pts = ConvertEntityPoints(e, -depthMeter);

        int segCount = e.closed && pts.Count > 2 ? pts.Count : pts.Count - 1;
        int created = 0;

        for (int i = 0; i < segCount; i++)
        {
            Vector3 a = pts[i];
            Vector3 b = pts[(i + 1) % pts.Count];

            float len = Vector3.Distance(a, b);
            if (len < 0.08f)
                continue;

            Vector3 mid = (a + b) * 0.5f;
            Vector3 dir = (b - a).normalized;

            GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
            beam.name = "C605_WALE_VISIBLE_2H_" + levelName + "_" + created;
            beam.transform.SetParent(group.transform, false);

            beam.transform.position = mid;

            // 일단 확실히 보이게 크게 표현
            beam.transform.localScale = new Vector3(
                Mathf.Max(waleWidth, 0.85f),
                Mathf.Max(waleHeight, 0.45f),
                len
            );

            beam.transform.rotation = Quaternion.LookRotation(dir, Vector3.up);

            // PF 벽과 겹치지 않도록 오른쪽 방향으로 살짝 띄움
            beam.transform.position += beam.transform.right * 0.45f;

            Renderer r = beam.GetComponent<Renderer>();
            if (waleMaterial != null)
            {
                r.material = waleMaterial;
            }
            else
            {
                Material mat = new Material(GetWebSafeShader());
                mat.color = new Color(1f, 0.75f, 0f, 1f);
                r.material = mat;
            }

            created++;
        }

        return created;
    }

    private Vector3 GetEntityCenterPoint(WangsukDxfEntity e, float y)
    {
        Vector3 sum = Vector3.zero;
        int count = 0;

        if (e == null || e.points == null)
            return Vector3.zero;

        foreach (var p in e.points)
        {
            Vector3 v = CadCoordinateSystem.ToUnityPoint(p);
            sum += v;
            count++;
        }

        if (count <= 0)
            return Vector3.zero;

        Vector3 center = sum / count;
        center.y = y;
        return center;
    }

    private void BuildWaleLevelsByPfCenters(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("WALE 중심점 생성 실패: PF JSON 데이터 없음");
            return;
        }

        GameObject group = registry.GetGroup(groupKey);

        if (group == null)
        {
            GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
            if (root == null)
                root = new GameObject("Wangsuk_CAD_3D_ROOT");

            group = new GameObject("WALE");
            group.transform.SetParent(root.transform, false);

            Debug.LogWarning("WALE 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var e in data.entities)
        {
            if (!e.has_points || e.points == null || e.points.Count < 2)
                continue;

            centers.Add(GetEntityCenterPoint(e, 0f));
        }

        int created = 0;

        for (int i = 0; i < centers.Count - 1; i++)
        {
            int pfNo = i + 1;
            int levels = GetWaleLevelByPfNo(pfNo);

            Vector3 a = centers[i];
            Vector3 b = centers[i + 1];

            float dist = Vector3.Distance(a, b);

            // 너무 큰 점프는 DXF 순서가 끊긴 구간일 가능성이 있어 제외
            if (dist > 20f)
                continue;

            // 코너에서 띠장이 서로 과하게 겹쳐 삼각형처럼 보이는 현상 완화
            Vector3 trimDir = (b - a).normalized;
            float trim = Mathf.Min(0.25f, dist * 0.20f);
            a += trimDir * trim;
            b -= trimDir * trim;

            if (levels >= 1)
                created += CreateWaleBeamBetweenCenters(group, a, b, waleDepth1, "P" + pfNo.ToString("000") + "_L1_0.6m");

            if (levels >= 2)
                created += CreateWaleBeamBetweenCenters(group, a, b, waleDepth2, "P" + pfNo.ToString("000") + "_L2_3.6m");

            if (levels >= 3)
                created += CreateWaleBeamBetweenCenters(group, a, b, waleDepth3, "P" + pfNo.ToString("000") + "_L3_5.6m");
        }

        Debug.Log("========== WALE 중심점 생성 진단 ==========");
        Debug.Log("PF center count = " + centers.Count);
        Debug.Log("C605 WALE 중심점 기반 생성 = " + created);
        Debug.Log("WALE 기준: C-612~C-619 전개도 재검토 기준: P248~P428=4단 후보 반영, 기타=3단 검토");
        Debug.Log("========================================");
    }

    private int CreateWaleBeamBetweenCenters(GameObject group, Vector3 a, Vector3 b, float depthMeter, string levelName)
    {
        if (group == null)
            return 0;

        a.y = -depthMeter;
        b.y = -depthMeter;

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.05f)
            return 0;

        Vector3 mid = (a + b) * 0.5f;

        GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
        beam.name = "C605_WALE_CENTER_2H_" + levelName;
        beam.transform.SetParent(group.transform, false);

        beam.transform.position = mid;

        // 2H 띠장처럼 눈에 보이게 두껍게 표현
        beam.transform.localScale = new Vector3(1.05f, 0.55f, len);
        beam.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(1f, 0.72f, 0f, 1f);
        beam.GetComponent<Renderer>().material = mat;

        return 1;
    }


    private void BuildStrutPlanFromDxf(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("C605 STRUT PLAN JSON 없음 또는 비어 있음: " + fileName);
            return;
        }

        GameObject group = registry.GetGroup(groupKey);

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        if (group == null)
        {
            group = new GameObject(groupKey);
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning(groupKey + " 그룹이 없어 강제 생성했습니다.");
        }

        GameObject cornerGroup = registry.GetGroup("CORNER_STRUT_L1");
        if (cornerGroup == null)
        {
            cornerGroup = new GameObject("CORNER_STRUT_L1");
            cornerGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("CORNER_STRUT_L1 그룹이 없어 강제 생성했습니다.");
        }

        int strutCreated = 0;
        int beamBracingCreated = 0;

        // STRUT / CORNER STRUT 수직 단수는 전개도 WALE 단수 기준으로 맞춘다.
        // 평면 위치는 C-605 STRUT / BEAM-BRACING 도형 그대로 사용.
        List<Vector3> pfCentersForStrutLevels = LoadPfCentersForStrutLevelMatching();

        foreach (var e in data.entities)
        {
            if (!e.has_points || e.points == null || e.points.Count < 2)
                continue;

            string layer = e.layer != null ? e.layer.ToUpper() : "";

            if (layer.Contains("BEAM-BRACING"))
            {
                // C-605 BEAM-BRACING 검토 결과:
                // 긴 부재 2개는 코너 스트러트 본체, 짧은 200mm급 부재 2개는 단부/보강선 후보.
                // Unity 좌표 변환 후 길이가 0.5 미만인 것은 단부선으로 보고 일단 제외. C-605 검토상 0.861 부재는 코너스트러트 본체.
                List<Vector3> checkPts = ConvertEntityPoints(e, -waleDepth1);

                if (checkPts == null || checkPts.Count < 2)
                    continue;

                float checkLen = Vector3.Distance(checkPts[0], checkPts[checkPts.Count - 1]);

                if (checkLen < 0.5f)
                {
                    Debug.Log("BEAM-BRACING 짧은 단부/보강선 제외: len=" + checkLen.ToString("F3"));
                    continue;
                }

                int levelCount = GetStrutLevelCountByNearestPf(e, pfCentersForStrutLevels);
                beamBracingCreated += CreateStrutPlanPolylineByWaleLevels(cornerGroup, e, "CORNER_STRUT_BODY", true, levelCount);
            }
            else
            {
                int levelCount = GetStrutLevelCountByNearestPf(e, pfCentersForStrutLevels);
                strutCreated += CreateStrutPlanPolylineByWaleLevels(group, e, "STRUT_BODY", false, levelCount);
            }
        }

        Debug.Log("========== C605 STRUT / CORNER STRUT 생성 ==========");
        Debug.Log("STRUT_L1 일반 버팀 본체 생성: " + strutCreated);
        Debug.Log("CORNER_STRUT_L1 본체 생성: " + beamBracingCreated);
        Debug.Log("도면 기준: STRUT/CORNER STRUT 평면 위치는 C-605 기준, 수직 단수는 WALE 단수 기준으로 2단/3단 생성.");
        Debug.Log("========================================");
    }

    private int CreateStrutPlanPolyline(GameObject group, WangsukDxfEntity e, float y, string label, bool isBeamBracing)
    {
        List<Vector3> pts = ConvertEntityPoints(e, y);

        int segCount = e.closed && pts.Count > 2 ? pts.Count : pts.Count - 1;
        int created = 0;

        Material mat = new Material(GetWebSafeShader());

        if (isBeamBracing)
            mat.color = new Color(1.0f, 0.05f, 0.75f, 1f);   // 코너/대각 후보: 진한 분홍
        else
            mat.color = new Color(0.65f, 0.1f, 1.0f, 1f);     // 일반 버팀: 보라

        for (int i = 0; i < segCount; i++)
        {
            Vector3 a = pts[i];
            Vector3 b = pts[(i + 1) % pts.Count];

            Vector3 dir = b - a;
            float len = dir.magnitude;

            if (len < 0.20f)
                continue;

            // 코너에서 세그먼트가 과도하게 겹쳐 삼각형처럼 보이는 현상 방지
            Vector3 forward = dir.normalized;
            float endTrim = Mathf.Min(0.20f, len * 0.25f);
            a += forward * endTrim;
            b -= forward * endTrim;

            dir = b - a;
            len = dir.magnitude;

            if (len < 0.10f)
                continue;

            GameObject beam = GameObject.CreatePrimitive(PrimitiveType.Cube);
            beam.name = "C605_" + label + "_" + created;
            beam.transform.SetParent(group.transform, false);

            beam.transform.position = (a + b) * 0.5f;

            // 검토용이라 우선 눈에 보이게 표현
            float width = isBeamBracing ? 0.90f : 0.65f;
            float height = isBeamBracing ? 0.70f : 0.55f;

            beam.transform.localScale = new Vector3(width, height, len);
            beam.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);
            beam.GetComponent<Renderer>().material = mat;

            created++;
        }

        return created;
    }


    
    




    private class AnchorSpecRange
    {
        public int startNo;
        public int endNo;
        public string source;
        public int level;
        public int step;
        public int skipStart;
        public int skipEnd;
        public bool enabled;

        public AnchorSpecRange(int s, int e, string src, int lv, int interval, int skipS, int skipE, bool use)
        {
            startNo = s;
            endNo = e;
            source = src;
            level = lv;
            step = interval;
            skipStart = skipS;
            skipEnd = skipE;
            enabled = use;
        }
    }



    
    


    
    
    
    



private void BuildElevationRulerFromModelBounds()
{
    GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
    if (root == null)
    {
        Debug.LogWarning("[ELEVATION_RULER] Wangsuk_CAD_3D_ROOT 없음");
        return;
    }

    GameObject group = FindGameObjectIncludingInactive("ELEVATION_RULER");
    if (group == null)
    {
        group = new GameObject("ELEVATION_RULER");
        group.transform.SetParent(root.transform, false);
    }

    for (int i = group.transform.childCount - 1; i >= 0; i--)
        DestroyImmediate(group.transform.GetChild(i).gameObject);

    Bounds modelBounds = new Bounds();
    bool hasBounds = false;

    Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
    foreach (Renderer r in renderers)
    {
        if (r == null) continue;

        string n = r.gameObject.name.ToUpper();
        string p = r.transform.parent != null ? r.transform.parent.name.ToUpper() : "";

        if (n.Contains("ELEVATION_RULER") || p.Contains("ELEVATION_RULER"))
            continue;
        if (n.Contains("UI") || p.Contains("UI"))
            continue;
        if (n.Contains("TEXT") || p.Contains("TEXT"))
            continue;
        if (n.Contains("ANCHOR") || p.Contains("ANCHOR"))
            continue;

        if (!hasBounds)
        {
            modelBounds = r.bounds;
            hasBounds = true;
        }
        else
        {
            modelBounds.Encapsulate(r.bounds);
        }
    }

    if (!hasBounds)
    {
        Debug.LogWarning("[ELEVATION_RULER] Bounds 계산 실패");
        return;
    }

    float bottomY = modelBounds.min.y;

    GameObject bottomObj = FindGameObjectIncludingInactive("EXCAVATION_BOTTOM");
    if (bottomObj != null)
    {
        Renderer[] brs = bottomObj.GetComponentsInChildren<Renderer>(true);
        Bounds bb = new Bounds();
        bool hasBottom = false;

        foreach (Renderer r in brs)
        {
            if (r == null) continue;

            if (!hasBottom)
            {
                bb = r.bounds;
                hasBottom = true;
            }
            else
            {
                bb.Encapsulate(r.bounds);
            }
        }

        if (hasBottom)
            bottomY = bb.center.y;
    }

    float topY = modelBounds.max.y;
    float height = topY - bottomY;

    if (height <= 0.1f)
    {
        Debug.LogWarning("[ELEVATION_RULER] 높이 계산값 이상: " + height);
        return;
    }

    // 핵심 수정:
    // 전체 모델 Bounds가 아니라 실제 PF 중심선 범위를 기준으로 기준자를 붙인다.
    WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup("c605_pf_hpile.json");

    float minX = modelBounds.min.x;
    float maxX = modelBounds.max.x;
    float minZ = modelBounds.min.z;
    float maxZ = modelBounds.max.z;
    Vector3 pfCenter = modelBounds.center;

    if (pfData != null && pfData.entities != null && pfData.entities.Count > 0)
    {
        bool first = true;
        Vector3 sum = Vector3.zero;
        int count = 0;

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, bottomY);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 c = Vector3.zero;
            foreach (var p in pts)
                c += p;
            c /= pts.Count;

            if (first)
            {
                minX = maxX = c.x;
                minZ = maxZ = c.z;
                first = false;
            }
            else
            {
                minX = Mathf.Min(minX, c.x);
                maxX = Mathf.Max(maxX, c.x);
                minZ = Mathf.Min(minZ, c.z);
                maxZ = Mathf.Max(maxZ, c.z);
            }

            sum += c;
            count++;
        }

        if (count > 0)
            pfCenter = sum / count;

        Debug.Log("[ELEVATION_RULER] PF 기준 Bounds 적용 / PF count = " + count);
    }
    else
    {
        Debug.LogWarning("[ELEVATION_RULER] PF JSON 없음. 모델 Bounds 기준 fallback");
    }

    int maxMeter = Mathf.CeilToInt(height);

    // 아주 가까이 붙임. 겹치면 0.06f로 올리면 됨.
    float offset = -0.02f; // 포스트파일에 더 밀착

    float boardWidth = 0.58f;
    float boardThickness = 0.026f;
    float textZ = -(boardThickness * 0.5f + 0.008f);

    float tickThin = 0.022f;
    float majorTickLen = 0.26f;
    float minorTickLen = 0.15f;

    float meterChar = 0.060f;
    float capChar = 0.085f;

    int meterFontSize = 54;
    int capFontSize = 72;

    Font font = KoreanFontProvider.Get();
    if (font == null)
        font = KoreanFontProvider.Get();

    Material whiteMat = new Material(GetWebSafeShader());
    whiteMat.color = Color.white;

    Material blackMat = new Material(GetWebSafeShader());
    blackMat.color = Color.black;

    Material redMat = new Material(GetWebSafeShader());
    redMat.color = Color.red;

    void SetupText(TextMesh tm, Color c)
    {
        tm.font = font;
        tm.fontStyle = FontStyle.Bold;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = c;

        MeshRenderer mr = tm.GetComponent<MeshRenderer>();
        if (mr != null && font != null)
            mr.sharedMaterial = font.material;
    }

    void CreateText(Transform parent, string name, string value, Vector3 localPos, float charSize, int fontSize, Color color)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;

        // 바깥쪽에서 정방향으로 읽히게 유지
        go.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);

        TextMesh tm = go.AddComponent<TextMesh>();
        tm.text = value;
        tm.characterSize = charSize;
        tm.fontSize = fontSize;
        SetupText(tm, color);
    }

    void CreateRuler(string rulerName, Vector3 basePos, Vector3 outward)
    {
        GameObject ruler = new GameObject(rulerName);
        ruler.transform.SetParent(group.transform, false);
        ruler.transform.position = new Vector3(basePos.x, bottomY, basePos.z);
        ruler.transform.rotation = Quaternion.LookRotation(outward, Vector3.up);

        GameObject panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
        panel.name = "Panel";
        panel.transform.SetParent(ruler.transform, false);
        panel.transform.localPosition = new Vector3(0f, height * 0.5f, 0f);
        panel.transform.localRotation = Quaternion.identity;
        panel.transform.localScale = new Vector3(boardWidth, height + 0.20f, boardThickness);
        panel.GetComponent<MeshRenderer>().sharedMaterial = whiteMat;
        DestroyImmediate(panel.GetComponent<Collider>());

        GameObject spine = GameObject.CreatePrimitive(PrimitiveType.Cube);
        spine.name = "Spine";
        spine.transform.SetParent(ruler.transform, false);
        spine.transform.localPosition = new Vector3(0f, height * 0.5f, -0.004f);
        spine.transform.localRotation = Quaternion.identity;
        spine.transform.localScale = new Vector3(0.012f, height, 0.008f);
        spine.GetComponent<MeshRenderer>().sharedMaterial = blackMat;
        DestroyImmediate(spine.GetComponent<Collider>());

        for (int m = 0; m <= maxMeter; m++)
        {
            float y = Mathf.Min((float)m, height);
            float tickLen = (m == 0 || m == maxMeter || m % 5 == 0) ? majorTickLen : minorTickLen;

            GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tick.name = "Tick_" + m;
            tick.transform.SetParent(ruler.transform, false);
            tick.transform.localPosition = new Vector3(0f, y, -0.005f);
            tick.transform.localRotation = Quaternion.identity;
            tick.transform.localScale = new Vector3(tickLen, tickThin, 0.008f);
            tick.GetComponent<MeshRenderer>().sharedMaterial = (m == 0) ? redMat : blackMat;
            DestroyImmediate(tick.GetComponent<Collider>());

            CreateText(
                ruler.transform,
                "Text_" + m,
                m.ToString() + "m",
                new Vector3(0f, y, textZ),
                meterChar,
                meterFontSize,
                (m == 0) ? Color.red : Color.black
            );
        }

        CreateText(
            ruler.transform,
            "CapText",
            "CAP " + height.ToString("0.0") + "m",
            new Vector3(0f, height + 0.22f, textZ),
            capChar,
            capFontSize,
            new Color(0.0f, 0.78f, 0.16f, 1f)
        );
    }

    // PF 외곽 바로 옆 4면 중앙
    Vector3 leftCenter   = new Vector3(minX - offset, 0f, pfCenter.z);
    Vector3 rightCenter  = new Vector3(maxX + offset, 0f, pfCenter.z);
    Vector3 bottomCenter = new Vector3(pfCenter.x, 0f, minZ - offset);
    Vector3 topCenter    = new Vector3(pfCenter.x, 0f, maxZ + offset);

    CreateRuler("RULER_LEFT",   leftCenter,   Vector3.left);
    CreateRuler("RULER_RIGHT",  rightCenter,  Vector3.right);
    CreateRuler("RULER_BOTTOM", bottomCenter, Vector3.back);
    CreateRuler("RULER_TOP",    topCenter,    Vector3.forward);

    group.SetActive(true);

    Debug.Log("========== ELEVATION_RULER PF 밀착 재생성 ==========");
    Debug.Log("[ELEVATION_RULER] PF minX/maxX/minZ/maxZ = " + minX + " / " + maxX + " / " + minZ + " / " + maxZ);
    Debug.Log("[ELEVATION_RULER] offset = " + offset);
    Debug.Log("[ELEVATION_RULER] bottomY = " + bottomY + " / topY = " + topY + " / height = " + height);
    Debug.Log("[ELEVATION_RULER] PF 외곽 기준 아주 가까이 배치 완료");
    Debug.Log("==================================================");
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




    
    
    private void BuildOneElevationRuler(
        GameObject parent,
        Vector3 basePos,
        string label,
        Vector3 modelCenter,
        float bottomY,
        float topY,
        float height,
        Material poleMat,
        Material tickMat,
        Material boardMat,
        Material zeroMat,
        Material capMat)
    {
        GameObject holder = new GameObject("HEIGHT_RULER_" + label);
        holder.transform.SetParent(parent.transform, false);

        Vector3 towardCenter = modelCenter - basePos;
        towardCenter.y = 0f;
        if (towardCenter.sqrMagnitude < 0.001f)
            towardCenter = Vector3.right;
        towardCenter.Normalize();

        // 수직 흰색 기준봉
        float poleRadius = 0.12f;

        GameObject pole = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        pole.name = "HEIGHT_POLE_" + label;
        pole.transform.SetParent(holder.transform, false);
        pole.transform.position = new Vector3(basePos.x, bottomY + height * 0.5f, basePos.z);
        pole.transform.localScale = new Vector3(poleRadius, height * 0.5f, poleRadius);

        Renderer pr = pole.GetComponent<Renderer>();
        if (pr != null)
        {
            pr.sharedMaterial = poleMat;
            pr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            pr.receiveShadows = false;
        }

        Collider pc = pole.GetComponent<Collider>();
        if (pc != null)
            DestroyImmediate(pc);

        int maxMeter = Mathf.CeilToInt(height);

        // 전체 라벨용 흰색 배경판: 검정글씨가 잘 보이게
        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "HEIGHT_WHITE_BOARD_" + label;
        board.transform.SetParent(holder.transform, false);
        board.transform.position = new Vector3(basePos.x, bottomY + height * 0.5f, basePos.z) + towardCenter * 1.85f;
        board.transform.localScale = new Vector3(2.15f, height + 1.25f, 0.055f);
        board.transform.rotation = Quaternion.LookRotation(towardCenter, Vector3.up);

        Renderer br = board.GetComponent<Renderer>();
        if (br != null)
        {
            br.sharedMaterial = boardMat;
            br.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            br.receiveShadows = false;
        }

        Collider bc = board.GetComponent<Collider>();
        if (bc != null)
            DestroyImmediate(bc);

        for (int m = 0; m <= maxMeter; m++)
        {
            float y = bottomY + m;
            if (y > topY + 0.01f)
                continue;

            bool isZero = m == 0;
            bool isFive = m % 5 == 0;

            float tickLen = isZero ? 1.45f : (isFive ? 1.20f : 0.75f);
            float tickThickness = isZero ? 0.070f : (isFive ? 0.055f : 0.035f);

            GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tick.name = "HEIGHT_TICK_" + m.ToString("00") + "m_" + label;
            tick.transform.SetParent(holder.transform, false);
            tick.transform.position = new Vector3(basePos.x, y, basePos.z) + towardCenter * (tickLen * 0.5f);
            tick.transform.localScale = new Vector3(tickLen, tickThickness, tickThickness);
            tick.transform.rotation = Quaternion.FromToRotation(Vector3.right, towardCenter);

            Renderer tr = tick.GetComponent<Renderer>();
            if (tr != null)
            {
                tr.sharedMaterial = isZero ? zeroMat : tickMat;
                tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                tr.receiveShadows = false;
            }

            Collider tc = tick.GetComponent<Collider>();
            if (tc != null)
                DestroyImmediate(tc);

            // 모든 1m 라벨 표시
            Color textColor = isZero ? new Color(1.0f, 0.0f, 0.0f, 1f) : Color.black;
            float textSize = isZero || isFive ? 0.36f : 0.28f;

            CreateElevationRulerText(
                holder,
                m.ToString() + "m",
                new Vector3(basePos.x, y, basePos.z) + towardCenter * 2.00f,
                modelCenter,
                textSize,
                textColor
            );
        }

        // 최상단 표시
        CreateElevationRulerText(
            holder,
            "CAP " + height.ToString("0.0") + "m",
            new Vector3(basePos.x, topY + 0.45f, basePos.z) + towardCenter * 2.00f,
            modelCenter,
            0.34f,
            new Color(0.00f, 0.55f, 0.15f, 1f)
        );

        GameObject topMarker = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        topMarker.name = "HEIGHT_CAP_MARKER_" + label;
        topMarker.transform.SetParent(holder.transform, false);
        topMarker.transform.position = new Vector3(basePos.x, topY, basePos.z);
        topMarker.transform.localScale = Vector3.one * 0.38f;

        Renderer mr = topMarker.GetComponent<Renderer>();
        if (mr != null)
        {
            mr.sharedMaterial = capMat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }

        Collider mc = topMarker.GetComponent<Collider>();
        if (mc != null)
            DestroyImmediate(mc);
    }



    
    
    
    
private void CreateElevationRulerText(GameObject parent, string text, Vector3 pos, Vector3 outward, float size, Color color)
{
    GameObject obj = new GameObject("HEIGHT_TEXT_" + text);
    obj.transform.SetParent(parent.transform, false);
    obj.transform.position = pos;

    TextMesh tm = obj.AddComponent<TextMesh>();
    tm.text = text;
    tm.fontSize = 320;
    tm.characterSize = size;
    tm.anchor = TextAnchor.MiddleCenter;
    tm.alignment = TextAlignment.Center;
    tm.color = color;
    tm.richText = false;
    tm.fontStyle = FontStyle.Bold;

    Font font = KoreanFontProvider.Get();
    if (font != null)
    {
        tm.font = font;
        MeshRenderer mr = obj.GetComponent<MeshRenderer>();
        if (mr != null)
        {
            mr.sharedMaterial = font.material;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }
    }

    // 숫자 방향 다시 반대로 회전
    obj.transform.rotation = Quaternion.LookRotation(-outward, Vector3.up);
}






    private Material CreateElevationRulerOpaqueMaterial(Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = color;
        mat.SetFloat("_Glossiness", 0f);
        return mat;
    }

    
    
    private Material CreateElevationRulerMaterial(Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = color;

        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);

        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");

        mat.renderQueue = 3300;
        return mat;
    }




    private void BuildAnchorSpecReviewFromPfCenters(string pfFileName, string groupKey)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null || pfData.entities.Count == 0)
        {
            Debug.LogError("[ANCHOR_SPEC] PF JSON 없음 또는 비어 있음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup(groupKey);
        if (group == null)
        {
            group = new GameObject(groupKey);
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning(groupKey + " 그룹이 없어 강제 생성했습니다.");
        }

        // 기존 앵커 중복 제거
        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        GameObject l1Group = new GameObject("ANCHOR_L1_LEVEL");
        GameObject l2Group = new GameObject("ANCHOR_L2_LEVEL");
        GameObject l3Group = new GameObject("ANCHOR_L3_LEVEL");

        l1Group.transform.SetParent(group.transform, false);
        l2Group.transform.SetParent(group.transform, false);
        l3Group.transform.SetParent(group.transform, false);

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("[ANCHOR_SPEC] PF center 부족: " + centers.Count);
            return;
        }

        Vector3 globalCenter = Vector3.zero;
        foreach (var c in centers)
            globalCenter += c;
        globalCenter /= centers.Count;

        // 띠장 중심 높이 기준. 실패 시 검토용 기본값 적용
        float y1 = -1.00f;
        float y2 = -3.00f;
        float y3 = -5.00f;

        try { y1 = -GetWaleSpecDepthByBand(1); } catch { y1 = -1.00f; }
        try { y2 = -GetWaleSpecDepthByBand(2); } catch { y2 = y1 - 2.00f; }
        try { y3 = -GetWaleSpecDepthByBand(3); } catch { y3 = y2 - 2.00f; }

        // 더 얇고 더 투명하게
        Material anchorMatL1 = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.18f));
        Material anchorMatL2 = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.15f));
        Material anchorMatL3 = CreateAnchorSpecMaterial(new Color(0.95f, 1.0f, 0.05f, 0.12f));
        Material headMat = CreateAnchorSpecMaterial(new Color(1.0f, 0.18f, 0.02f, 0.28f));

        // 도면 기준 적용:
        // 전개도 @토목-앵커 레이어 = 설치 구간 확인
        // 단면도 1/2/3단 표기 + 띠장 단수 = 단수/높이 기준
        AnchorSpecRange[] ranges = new AnchorSpecRange[]
        {
            // 1단: 전개도 앵커 구간 전체
            new AnchorSpecRange(1,   67,  "C-612", 1, 5, 2, 2, true),
            new AnchorSpecRange(67,  131, "C-613", 1, 5, 2, 2, true),
            new AnchorSpecRange(131, 196, "C-614", 1, 5, 2, 2, true),
            new AnchorSpecRange(196, 248, "C-615", 1, 5, 2, 2, true),
            new AnchorSpecRange(248, 306, "C-616", 1, 5, 2, 2, true),
            new AnchorSpecRange(306, 365, "C-617", 1, 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 1, 5, 2, 2, true),
            new AnchorSpecRange(428, 492, "C-619", 1, 5, 2, 3, true),

            // 2단: 2단 띠장 존재 구간
            new AnchorSpecRange(1,   67,  "C-612", 2, 5, 2, 2, true),
            new AnchorSpecRange(67,  131, "C-613", 2, 5, 2, 2, true),
            new AnchorSpecRange(131, 196, "C-614", 2, 5, 2, 2, true),
            new AnchorSpecRange(196, 248, "C-615", 2, 5, 2, 2, true),
            new AnchorSpecRange(248, 306, "C-616", 2, 5, 2, 2, true),
            new AnchorSpecRange(306, 365, "C-617", 2, 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 2, 5, 2, 2, true),
            new AnchorSpecRange(428, 492, "C-619", 2, 5, 2, 3, true),

            // 3단: 3단 띠장/단면 확인 구간
            // 일부 구간은 도면검토 기준으로 부분 적용
            new AnchorSpecRange(95,  116, "C-613", 3, 5, 1, 1, true),
            new AnchorSpecRange(178, 196, "C-614", 3, 5, 1, 1, true),
            new AnchorSpecRange(196, 248, "C-615", 3, 5, 2, 2, true),
            new AnchorSpecRange(248, 258, "C-616A", 3, 5, 1, 1, true),
            new AnchorSpecRange(278, 306, "C-616B", 3, 5, 1, 1, true),
            new AnchorSpecRange(306, 365, "C-617", 3, 5, 3, 2, true),
            new AnchorSpecRange(365, 428, "C-618", 3, 5, 2, 2, true),
            new AnchorSpecRange(428, 469, "C-619", 3, 5, 2, 2, true)
        };

        int createdL1 = 0;
        int createdL2 = 0;
        int createdL3 = 0;

        foreach (var r in ranges)
        {
            if (!r.enabled)
                continue;

            GameObject targetGroup = l1Group;
            float y = y1;
            Material mat = anchorMatL1;

            if (r.level == 2)
            {
                targetGroup = l2Group;
                y = y2;
                mat = anchorMatL2;
            }
            else if (r.level == 3)
            {
                targetGroup = l3Group;
                y = y3;
                mat = anchorMatL3;
            }

            int made = CreateAnchorSpecRange(targetGroup, centers, globalCenter, r, y, mat, headMat);

            if (r.level == 1) createdL1 += made;
            else if (r.level == 2) createdL2 += made;
            else if (r.level == 3) createdL3 += made;
        }

        group.SetActive(false);

        Debug.Log("========== ANCHOR_SPEC_REVIEW 1/2/3단 도면기준 생성 ==========");
        Debug.Log("[ANCHOR_SPEC] PF center count: " + centers.Count);
        Debug.Log("[ANCHOR_SPEC] L1 생성: " + createdL1 + " / y=" + y1);
        Debug.Log("[ANCHOR_SPEC] L2 생성: " + createdL2 + " / y=" + y2);
        Debug.Log("[ANCHOR_SPEC] L3 생성: " + createdL3 + " / y=" + y3);
        Debug.Log("[ANCHOR_SPEC] 기준: 전개도 @토목-앵커 구간 + 단면도 1/2/3단 + 띠장 단수 높이");
        Debug.Log("[ANCHOR_SPEC] 표시: 더 얇게 / 더 투명하게 / 4단은 미생성");
        Debug.Log("=============================================================");
    }



    
    
    private int CreateAnchorSpecRange(
        GameObject group,
        List<Vector3> centers,
        Vector3 globalCenter,
        AnchorSpecRange range,
        float anchorY,
        Material anchorMat,
        Material headMat)
    {
        int created = 0;

        int start = Mathf.Clamp(range.startNo + range.skipStart, 1, centers.Count);
        int end = Mathf.Clamp(range.endNo - range.skipEnd, 1, centers.Count);

        if (end < start)
        {
            Debug.Log("[ANCHOR_SPEC] " + range.source + " L" + range.level + " 생성 없음: skip 범위 과다");
            return 0;
        }

        int step = Mathf.Max(1, range.step);

        for (int no = start; no <= end; no += step)
        {
            int idx = no - 1;
            if (idx < 0 || idx >= centers.Count)
                continue;

            Vector3 pf = centers[idx];

            int prevIdx = (idx - 1 + centers.Count) % centers.Count;
            int nextIdx = (idx + 1) % centers.Count;

            Vector3 prev = centers[prevIdx];
            Vector3 next = centers[nextIdx];

            Vector3 tangent = next - prev;
            tangent.y = 0f;

            if (tangent.sqrMagnitude < 0.0001f)
                continue;

            tangent.Normalize();

            Vector3 n1 = Vector3.Cross(Vector3.up, tangent).normalized;
            Vector3 n2 = -n1;

            Vector3 radialOut = pf - globalCenter;
            radialOut.y = 0f;

            if (radialOut.sqrMagnitude < 0.0001f)
                radialOut = n1;

            radialOut.Normalize();

            Vector3 outward = Vector3.Dot(n1, radialOut) >= Vector3.Dot(n2, radialOut) ? n1 : n2;
            outward = (outward * 0.78f + radialOut * 0.22f).normalized;

            // 단수가 내려갈수록 머리점이 살짝 더 바깥으로 보이도록 미세 오프셋
            float headOffset = 0.42f + (range.level - 1) * 0.05f;
            Vector3 head = new Vector3(pf.x, anchorY, pf.z) + outward * headOffset;

            float displayLen = 9.22f; // 도면 c605_anchor_l1.json 중앙값 9216mm 기준
            float downwardAngleDeg = 15.0f;
            float rad = downwardAngleDeg * Mathf.Deg2Rad;

            Vector3 slopedDir = outward * Mathf.Cos(rad) + Vector3.down * Mathf.Sin(rad);
            slopedDir.Normalize();

            Vector3 tail = head + slopedDir * displayLen;

            GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            anchor.name = "ANCHOR_L" + range.level + "_" + range.source + "_P" + no.ToString("000");
            anchor.transform.SetParent(group.transform, false);
            anchor.transform.position = (head + tail) * 0.5f;

            // 더 얇게
            anchor.transform.localScale = new Vector3(0.040f, 0.040f, displayLen);
            anchor.transform.rotation = Quaternion.LookRotation(slopedDir, Vector3.up);

            Renderer ar = anchor.GetComponent<Renderer>();
            if (ar != null)
            {
                ar.sharedMaterial = anchorMat;
                ar.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                ar.receiveShadows = false;
            }

            Collider ac = anchor.GetComponent<Collider>();
            if (ac != null)
                DestroyImmediate(ac);

            GameObject headSphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            headSphere.name = "ANCHOR_HEAD_L" + range.level + "_" + range.source + "_P" + no.ToString("000");
            headSphere.transform.SetParent(group.transform, false);
            headSphere.transform.position = head;

            // 머리점도 작게
            headSphere.transform.localScale = Vector3.one * 0.14f;

            Renderer hr = headSphere.GetComponent<Renderer>();
            if (hr != null)
            {
                hr.sharedMaterial = headMat;
                hr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                hr.receiveShadows = false;
            }

            Collider hc = headSphere.GetComponent<Collider>();
            if (hc != null)
                DestroyImmediate(hc);

            created++;
        }

        Debug.Log("[ANCHOR_SPEC] " + range.source + " L" + range.level + " P" + range.startNo.ToString("000") + "~P" + range.endNo.ToString("000") + " / step=" + range.step + " / 생성=" + created);
        return created;
    }



    
    
    
    private Material CreateAnchorSpecMaterial(Color color)
    {
        Material mat = new Material(GetWebSafeShader());
        mat.color = color;

        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);

        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");

        mat.renderQueue = 3200;
        return mat;
    }





    private void BuildAnchorL1FromDxf(string fileName, string groupKey)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(fileName);
        if (data == null || data.entities == null)
        {
            Debug.LogError("C605 ANCHOR JSON 없음 또는 비어 있음: " + fileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup(groupKey);
        if (group == null)
        {
            group = new GameObject(groupKey);
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning(groupKey + " 그룹이 없어 강제 생성했습니다.");
        }

        for (int i = group.transform.childCount - 1; i >= 0; i--)
            DestroyImmediate(group.transform.GetChild(i).gameObject);

        List<Vector3> pfCentersForAnchor = LoadPfCentersForAnchorHead();

        int createdL1 = 0;
        int skipped = 0;

        float anchorY = -1.00f;

        try
        {
            anchorY = -GetWaleSpecDepthByBand(1);
        }
        catch
        {
            anchorY = -1.00f;
        }

        Debug.Log("[ANCHOR] source entity count: " + data.entities.Count);
        Debug.Log("[ANCHOR] pf center count: " + pfCentersForAnchor.Count);
        Debug.Log("[ANCHOR] anchorY: " + anchorY);

        foreach (var e in data.entities)
        {
            int made = CreateAnchorPolyline(group, e, anchorY, "ANCHOR_L1_SPEC", pfCentersForAnchor);
            if (made > 0)
                createdL1 += made;
            else
                skipped++;
        }

        group.SetActive(false);

        Debug.Log("========== ANCHOR 도면기준 1차 보정 ==========");
        Debug.Log("ANCHOR_L1_SPEC 생성: " + createdL1);
        Debug.Log("ANCHOR 제외/스킵: " + skipped);
        Debug.Log("ANCHOR_L1 child count: " + group.transform.childCount);
        Debug.Log("기준: 1단 띠장 높이에 맞춤. 기존 L2/L3 자동 생성 중지.");
        Debug.Log("==============================================");
    }



    
    
    private int CreateAnchorPolyline(GameObject group, WangsukDxfEntity e, float y, string label, List<Vector3> pfCenters)
    {
        List<Vector3> pts = ConvertEntityPoints(e, y);
        if (pts == null || pts.Count < 2)
            return 0;

        Vector3 p0 = pts[0];
        Vector3 p1 = pts[pts.Count - 1];

        Vector3 anchorHead = p0;
        Vector3 anchorTail = p1;

        // PF/CIP 벽체에 가까운 끝점을 앙카 머리점으로 사용
        if (pfCenters != null && pfCenters.Count > 0)
        {
            float p0Dist = GetNearestDistanceXZ(p0, pfCenters);
            float p1Dist = GetNearestDistanceXZ(p1, pfCenters);

            if (p1Dist < p0Dist)
            {
                anchorHead = p1;
                anchorTail = p0;
            }

            float headDist = GetNearestDistanceXZ(anchorHead, pfCenters);

            // 기존 400f가 너무 강해서 전부 제외될 수 있으므로 완화
            // 그래도 너무 먼 도면기호는 제외
            if (headDist > 2500f)
                return 0;
        }

        Vector3 dir = anchorTail - anchorHead;
        dir.y = 0f;

        float originalLen = dir.magnitude;
        if (originalLen < 0.05f)
            return 0;

        dir.Normalize();

        // 화면 검토용: CAD 원본 길이가 짧아도 최소 8m 이상 보이게 강제
        float displayLen = Mathf.Clamp(originalLen, 8.45f, 9.22f);

        float downwardAngleDeg = 15.0f;
        float downwardRad = downwardAngleDeg * Mathf.Deg2Rad;

        Vector3 slopedDir = dir * Mathf.Cos(downwardRad) + Vector3.down * Mathf.Sin(downwardRad);
        slopedDir.Normalize();

        Vector3 a = new Vector3(anchorHead.x, y, anchorHead.z);
        Vector3 b = a + slopedDir * displayLen;

        GameObject anchor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        anchor.name = "C605_" + label;
        anchor.transform.SetParent(group.transform, false);
        anchor.transform.position = (a + b) * 0.5f;

        // 너무 얇으면 안 보이므로 굵게
        anchor.transform.localScale = new Vector3(0.22f, 0.22f, displayLen);
        anchor.transform.rotation = Quaternion.LookRotation(slopedDir, Vector3.up);

        Renderer r = anchor.GetComponent<Renderer>();
        if (r != null)
        {
            Material mat = new Material(GetWebSafeShader());
            mat.color = new Color(0.95f, 1.0f, 0.05f, 1f);
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        Collider c = anchor.GetComponent<Collider>();
        if (c != null)
            DestroyImmediate(c);

        // 머리점 표시: 띠장 접점 확인용
        GameObject head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        head.name = "ANCHOR_HEAD_" + label;
        head.transform.SetParent(group.transform, false);
        head.transform.position = a;
        head.transform.localScale = Vector3.one * 0.65f;

        Renderer hr = head.GetComponent<Renderer>();
        if (hr != null)
        {
            Material hm = new Material(GetWebSafeShader());
            hm.color = new Color(1.0f, 0.05f, 0.02f, 1f);
            hr.sharedMaterial = hm;
            hr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            hr.receiveShadows = false;
        }

        Collider hc = head.GetComponent<Collider>();
        if (hc != null)
            DestroyImmediate(hc);

        return 1;
    }




    private List<Vector3> LoadPfCentersForAnchorHead()
    {
        List<Vector3> centers = new List<Vector3>();

        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup("c605_pf_hpile.json");
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogWarning("ANCHOR 머리점 매칭용 PF JSON 없음");
            return centers;
        }

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, -waleDepth1);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        Debug.Log("ANCHOR 머리점 매칭용 PF center count = " + centers.Count);
        return centers;
    }

    private float GetNearestDistanceXZ(Vector3 p, List<Vector3> centers)
    {
        float best = float.MaxValue;

        foreach (var c in centers)
        {
            float dx = p.x - c.x;
            float dz = p.z - c.z;
            float d = dx * dx + dz * dz;

            if (d < best)
                best = d;
        }

        return best;
    }


    private int GetAnchorLevelCountByNearestPf(WangsukDxfEntity e, List<Vector3> pfCenters)
    {
        if (pfCenters == null || pfCenters.Count == 0)
            return 1;

        List<Vector3> pts = ConvertEntityPoints(e, -waleDepth1);
        if (pts == null || pts.Count < 2)
            return 1;

        Vector3 p0 = pts[0];
        Vector3 p1 = pts[pts.Count - 1];

        float p0Dist = GetNearestDistanceXZ(p0, pfCenters);
        float p1Dist = GetNearestDistanceXZ(p1, pfCenters);

        Vector3 anchorHead = p0;
        if (p1Dist < p0Dist)
            anchorHead = p1;

        int nearestIndex = 0;
        float best = float.MaxValue;

        for (int i = 0; i < pfCenters.Count; i++)
        {
            float dx = anchorHead.x - pfCenters[i].x;
            float dz = anchorHead.z - pfCenters[i].z;
            float d = dx * dx + dz * dz;

            if (d < best)
            {
                best = d;
                nearestIndex = i;
            }
        }

        int pfNo = nearestIndex + 1;

        // 전개도/띠장 검토 기준:
        // C-612~C-619 전개도 재검토 기준: P248~P428=4단 후보 반영, 기타=3단 검토
        if (pfNo >= 1 && pfNo <= 97)
            return 2;

        if (pfNo >= 98 && pfNo <= 365)
            return 3;

        if (pfNo >= 366 && pfNo <= 405)
            return 2;

        if (pfNo >= 406 && pfNo <= 492)
            return 3;

        return 1;
    }


    private List<Vector3> LoadPfCentersForStrutLevelMatching()
    {
        List<Vector3> centers = new List<Vector3>();

        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup("c605_pf_hpile.json");
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogWarning("STRUT 단수 매칭용 PF JSON 없음");
            return centers;
        }

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        Debug.Log("STRUT 단수 매칭용 PF center count = " + centers.Count);
        return centers;
    }

    private int GetStrutLevelCountByNearestPf(WangsukDxfEntity e, List<Vector3> pfCenters)
    {
        if (pfCenters == null || pfCenters.Count == 0)
            return 1;

        List<Vector3> pts = ConvertEntityPoints(e, 0f);
        if (pts == null || pts.Count == 0)
            return 1;

        Vector3 center = Vector3.zero;
        foreach (var p in pts)
            center += p;

        center /= pts.Count;

        int nearestIndex = 0;
        float bestDist = float.MaxValue;

        for (int i = 0; i < pfCenters.Count; i++)
        {
            float dx = center.x - pfCenters[i].x;
            float dz = center.z - pfCenters[i].z;
            float d = dx * dx + dz * dz;

            if (d < bestDist)
            {
                bestDist = d;
                nearestIndex = i;
            }
        }

        int pfNo = nearestIndex + 1;

        // WALE 전개도 검토 기준:
        // C-612~C-619 전개도 재검토 기준: P248~P428=4단 후보 반영, 기타=3단 검토
        if (pfNo >= 1 && pfNo <= 97)
            return 2;

        if (pfNo >= 98 && pfNo <= 365)
            return 3;

        if (pfNo >= 366 && pfNo <= 405)
            return 2;

        if (pfNo >= 406 && pfNo <= 492)
            return 3;

        return 1;
    }

    private int CreateStrutPlanPolylineByWaleLevels(GameObject group, WangsukDxfEntity e, string label, bool isBeamBracing, int levelCount)
    {
        int created = 0;

        created += CreateStrutPlanPolyline(group, e, -waleDepth1, label + "_L1", isBeamBracing);

        if (levelCount >= 2)
            created += CreateStrutPlanPolyline(group, e, -waleDepth2, label + "_L2", isBeamBracing);

        if (levelCount >= 3)
            created += CreateStrutPlanPolyline(group, e, -waleDepth3, label + "_L3", isBeamBracing);

        if (levelCount >= 4)
            created += CreateStrutPlanPolyline(group, e, -waleDepth4, label + "_L4", isBeamBracing);

        return created;
    }


    private void BuildExcavationFaceBottomAndText(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("굴착면 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject faceGroup = registry.GetGroup("EXCAVATION_FACE");
        if (faceGroup == null)
        {
            faceGroup = new GameObject("EXCAVATION_FACE");
            faceGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("EXCAVATION_FACE 그룹이 없어 강제 생성했습니다.");
        }

        GameObject bottomGroup = registry.GetGroup("EXCAVATION_BOTTOM");
        if (bottomGroup == null)
        {
            bottomGroup = new GameObject("EXCAVATION_BOTTOM");
            bottomGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("EXCAVATION_BOTTOM 그룹이 없어 강제 생성했습니다.");
        }

        GameObject textGroup = registry.GetGroup("BOTTOM_EL_TEXT");
        if (textGroup == null)
        {
            textGroup = new GameObject("BOTTOM_EL_TEXT");
            textGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("BOTTOM_EL_TEXT 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 3)
        {
            Debug.LogWarning("굴착면 생성 실패: PF center 부족");
            return;
        }

        // 현재 1차 기준값.
        // 도면 전개도/단면도에서 구간별 시공하한선 EL 확정 후 bottomY는 구간별로 보정 예정.
        float groundY = 0.0f;
        float bottomY = -8.0f;

        Material faceMat = new Material(GetWebSafeShader());
        faceMat.color = new Color(0.48f, 0.36f, 0.22f, 0.92f);

        Material bottomMat = new Material(GetWebSafeShader());
        bottomMat.color = new Color(0.58f, 0.52f, 0.43f, 1f);

        int faceCreated = 0;

        for (int i = 0; i < centers.Count - 1; i++)
        {
            Vector3 aTop = new Vector3(centers[i].x, groundY, centers[i].z);
            Vector3 bTop = new Vector3(centers[i + 1].x, groundY, centers[i + 1].z);

            float dist = Vector3.Distance(aTop, bTop);

            // DXF 순서가 크게 튀는 구간은 제외
            if (dist < 0.05f || dist > 20f)
                continue;

            Vector3 aBottom = new Vector3(aTop.x, bottomY, aTop.z);
            Vector3 bBottom = new Vector3(bTop.x, bottomY, bTop.z);

            CreateExcavationWallQuad(faceGroup, aTop, bTop, bBottom, aBottom, faceMat, "C605_EXCAVATION_FACE_" + faceCreated);
            faceCreated++;
        }

        int bottomCreated = CreateExcavationBottomMesh(bottomGroup, centers, bottomY, bottomMat);

        Vector3 center = Vector3.zero;
        foreach (var p in centers)
            center += p;
        center /= centers.Count;
        // 중앙 BOTTOM EL CHECK 테스트 글씨 제거
Debug.Log("========== C605 굴착면/바닥 생성 ==========");
        Debug.Log("EXCAVATION_FACE 벽면 생성: " + faceCreated);
        Debug.Log("EXCAVATION_BOTTOM 바닥 생성: " + bottomCreated);
        Debug.Log("BOTTOM_EL_TEXT 검정 글씨 생성: 1");
        Debug.Log("현재 기준: PF/H-PILE 중심선 기반, groundY=0, bottomY=-8.0. 실제 EL/토질/암질은 다음 단계에서 도면 기준 보정.");
        Debug.Log("==========================================");
    }

    private void CreateExcavationWallQuad(GameObject group, Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, Material mat, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = new Vector3[]
        {
            p0, p1, p2, p3
        };

        mesh.triangles = new int[]
        {
            0, 1, 2,
            0, 2, 3
        };

        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;
    }

    private int CreateExcavationBottomMesh(GameObject group, List<Vector3> centers, float bottomY, Material mat)
    {
        if (centers == null || centers.Count < 3)
            return 0;

        List<Vector3> hull = BuildConvexHullXZ(centers, bottomY);

        if (hull == null || hull.Count < 3)
        {
            Debug.LogWarning("굴착 바닥 Convex Hull 생성 실패");
            return 0;
        }

        Vector3 center = Vector3.zero;
        foreach (var p in hull)
            center += p;
        center /= hull.Count;

        List<Vector3> vertices = new List<Vector3>();
        vertices.Add(center);
        vertices.AddRange(hull);

        List<int> tris = new List<int>();

        for (int i = 1; i < vertices.Count; i++)
        {
            int next = i + 1;
            if (next >= vertices.Count)
                next = 1;

            tris.Add(0);
            tris.Add(i);
            tris.Add(next);
        }

        GameObject obj = new GameObject("C605_EXCAVATION_BOTTOM_SURFACE_HULL");
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = vertices.ToArray();
        mesh.triangles = tris.ToArray();
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;

        return 1;
    }

    private void CreateBlackWorldText(GameObject group, string text, Vector3 position, float size)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_BOTTOM_EL_TEXT_WHITE_PLATE";
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.02f, position.z);
        plate.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
        plate.transform.localScale = new Vector3(8.5f, 0.025f, 3.2f);

        Material plateMat = new Material(GetWebSafeShader());
        plateMat.color = Color.white;
        plate.GetComponent<Renderer>().material = plateMat;

        string line1 = "BOTTOM EL";
        string line2 = "CHECK";

        if (!string.IsNullOrEmpty(text))
        {
            string[] parts = text.Split('|');
            if (parts.Length >= 2)
            {
                line1 = parts[0];
                line2 = parts[1];
            }
        }

        Font arial = KoreanFontProvider.Get();

        CreateFlatBlackTextLine(group, line1, new Vector3(position.x, position.y + 0.10f, position.z + 0.45f), size, arial, "C605_BOTTOM_EL_TEXT_LINE_1");
        CreateFlatBlackTextLine(group, line2, new Vector3(position.x, position.y + 0.10f, position.z - 0.45f), size, arial, "C605_BOTTOM_EL_TEXT_LINE_2");
    }

    private void CreateFlatBlackTextLine(GameObject group, string label, Vector3 position, float size, Font font, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = position;

        // 바닥 위에 눕혀서 위에서 읽히도록 배치
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.095f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = font.material;
                mr.material.color = Color.black;
            }
        }
    }


    private List<Vector3> BuildConvexHullXZ(List<Vector3> points, float y)
    {
        List<Vector3> pts = new List<Vector3>();

        foreach (var p in points)
            pts.Add(new Vector3(p.x, y, p.z));

        pts.Sort((a, b) =>
        {
            int cx = a.x.CompareTo(b.x);
            if (cx != 0)
                return cx;
            return a.z.CompareTo(b.z);
        });

        List<Vector3> unique = new List<Vector3>();
        Vector3? last = null;

        foreach (var p in pts)
        {
            if (last == null || Vector3.Distance(p, last.Value) > 0.001f)
            {
                unique.Add(p);
                last = p;
            }
        }

        if (unique.Count < 3)
            return unique;

        List<Vector3> lower = new List<Vector3>();
        foreach (var p in unique)
        {
            while (lower.Count >= 2 && CrossXZ(lower[lower.Count - 2], lower[lower.Count - 1], p) <= 0f)
                lower.RemoveAt(lower.Count - 1);

            lower.Add(p);
        }

        List<Vector3> upper = new List<Vector3>();
        for (int i = unique.Count - 1; i >= 0; i--)
        {
            Vector3 p = unique[i];

            while (upper.Count >= 2 && CrossXZ(upper[upper.Count - 2], upper[upper.Count - 1], p) <= 0f)
                upper.RemoveAt(upper.Count - 1);

            upper.Add(p);
        }

        lower.RemoveAt(lower.Count - 1);
        upper.RemoveAt(upper.Count - 1);

        lower.AddRange(upper);

        return lower;
    }

    private float CrossXZ(Vector3 o, Vector3 a, Vector3 b)
    {
        return (a.x - o.x) * (b.z - o.z) - (a.z - o.z) * (b.x - o.x);
    }


    
private void CreateElevationRulerSide(Transform parent, string sideName, Vector3 basePos, Vector3 outward, float bottomY, float topY)
{
    GameObject side = new GameObject("RULER_" + sideName);
    side.transform.SetParent(parent, false);

    float totalHeight = topY - bottomY;

    float panelWidth = 1.55f;
    float panelDepth = 0.04f;
    float tickWidth = 0.34f;
    float tickHeight = 0.025f;
    float tickDepth = 0.025f;
    float textOffset = 0.06f;
    float labelSize = 0.16f;

    Quaternion rot = Quaternion.LookRotation(outward, Vector3.up);
    Vector3 panelCenter = new Vector3(basePos.x, (bottomY + topY) * 0.5f, basePos.z);

    Material whiteMat = new Material(GetWebSafeShader());
    whiteMat.color = Color.white;

    Material blackMat = new Material(GetWebSafeShader());
    blackMat.color = Color.black;

    Material redMat = new Material(GetWebSafeShader());
    redMat.color = Color.red;

    Material greenMat = new Material(GetWebSafeShader());
    greenMat.color = new Color(0.0f, 0.7f, 0.1f, 1f);

    // 메인 기준판
    GameObject panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
    panel.name = sideName + "_PANEL";
    panel.transform.SetParent(side.transform, false);
    panel.transform.position = panelCenter;
    panel.transform.rotation = rot;
    panel.transform.localScale = new Vector3(panelWidth, totalHeight, panelDepth);

    Renderer panelR = panel.GetComponent<Renderer>();
    if (panelR != null) panelR.material = whiteMat;

    // 1m 눈금
    int maxMeter = Mathf.CeilToInt(totalHeight);

    for (int i = 0; i <= maxMeter; i++)
    {
        float y = bottomY + i;
        if (y > topY + 0.001f) y = topY;

        Vector3 tickPos = new Vector3(basePos.x, y, basePos.z) + outward * 0.18f;

        GameObject tick = GameObject.CreatePrimitive(PrimitiveType.Cube);
        tick.name = sideName + "_TICK_" + i;
        tick.transform.SetParent(side.transform, false);
        tick.transform.position = tickPos;
        tick.transform.rotation = rot;
        tick.transform.localScale = new Vector3(tickWidth, tickHeight, tickDepth);

        Renderer tr = tick.GetComponent<Renderer>();
        if (tr != null)
            tr.material = (i == 0 ? redMat : blackMat);

        Color tc = (i == 0) ? Color.red : Color.black;
        string label = (i == 0) ? "0m" : (i.ToString() + "m");

        Vector3 textPos = tickPos + outward * textOffset;
        CreateElevationRulerText(side, label, textPos, outward, labelSize, tc);

        if (Mathf.Abs(y - topY) < 0.001f)
            break;
    }

    // CAP 표기
    float capHeight = totalHeight;
    Vector3 capPos = new Vector3(basePos.x, topY + 0.18f, basePos.z) + outward * 0.24f;
    CreateElevationRulerText(side, "CAP " + capHeight.ToString("0.0") + "m", capPos, outward, 0.18f, new Color(0.0f, 0.65f, 0.0f, 1f));
}

public void ToggleElevationRuler()
{
    GameObject group = FindGameObjectIncludingInactive("ELEVATION_RULER");
    if (group == null)
    {
        Debug.Log("[ELEVATION_RULER] 기존 그룹 없음 -> 새로 생성");
        BuildElevationRulerFromModelBounds();
        group = FindGameObjectIncludingInactive("ELEVATION_RULER");
    }

    if (group == null)
    {
        Debug.LogWarning("[ELEVATION_RULER] 생성 실패");
        return;
    }

    bool next = !group.activeSelf;
    group.SetActive(next);
    Debug.Log("[ELEVATION_RULER] 표시 상태: " + next);
}


private void BuildSoilRockBandsAndLabels(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("지층 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject layerGroup = registry.GetGroup("SOIL_ROCK_LAYER");
        if (layerGroup == null)
        {
            layerGroup = new GameObject("SOIL_ROCK_LAYER");
            layerGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("SOIL_ROCK_LAYER 그룹이 없어 강제 생성했습니다.");
        }

        GameObject textGroup = registry.GetGroup("SOIL_ROCK_TEXT");
        if (textGroup == null)
        {
            textGroup = new GameObject("SOIL_ROCK_TEXT");
            textGroup.transform.SetParent(root.transform, false);
            Debug.LogWarning("SOIL_ROCK_TEXT 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 3)
        {
            Debug.LogWarning("지층 생성 실패: PF center 부족");
            return;
        }

        // 현재 Unity 깊이 기준:
        // groundY = 0, bottomY = -8.0
        // 도면상 대표 굴착고는 대략 EL 39.50~41.00에서 시공하한선 EL 29.54~31.00 범위.
        // 1차 모델에서는 깊이비율로 지층을 표현하고, 추후 구간별 주상도 값으로 세분화.
        float groundY = 0.0f;
        float bottomY = -8.0f;

        float fillTop = groundY;
        float fillBottom = -1.40f;

        float sedimentTop = fillBottom;
        float sedimentBottom = -4.60f;

        float weatheredSoilTop = sedimentBottom;
        float weatheredSoilBottom = -6.20f;

        float weatheredRockTop = weatheredSoilBottom;
        float weatheredRockBottom = bottomY;

        Material mat = CreateSoilRockMaterial(new Color(0.45f, 0.25f, 0.08f, 0.26f));       // 매립층 - 반투명 진갈색
        Material sedimentMat = CreateSoilRockMaterial(new Color(0.78f, 0.55f, 0.22f, 0.24f));   // 퇴적층 - 반투명 황갈색
        Material wsMat = CreateSoilRockMaterial(new Color(0.95f, 0.72f, 0.18f, 0.24f));         // 풍화토 - 반투명 황토색
        Material wrMat = CreateSoilRockMaterial(new Color(0.34f, 0.34f, 0.32f, 0.28f));         // 풍화암 - 반투명 진회색

        int fillCount = CreateSoilBandAlongPf(layerGroup, centers, fillTop, fillBottom, mat, "SOIL_FILL");
        int sedimentCount = CreateSoilBandAlongPf(layerGroup, centers, sedimentTop, sedimentBottom, sedimentMat, "SOIL_SEDIMENT");
        int wsCount = CreateSoilBandAlongPf(layerGroup, centers, weatheredSoilTop, weatheredSoilBottom, wsMat, "SOIL_WEATHERED_SOIL");
        int wrCount = CreateSoilBandAlongPf(layerGroup, centers, weatheredRockTop, weatheredRockBottom, wrMat, "SOIL_WEATHERED_ROCK");

        Vector3 center = Vector3.zero;
        foreach (var p in centers)
            center += p;
        center /= centers.Count;

        // 바닥 위 검정 글씨. 한글 표시를 위해 Malgun Gothic 동적 폰트 사용.
        // 중앙 지층 글씨 제거
        // 중앙 지층 글씨 제거
        // 중앙 지층 글씨 제거
        // 중앙 지층 글씨 제거
        // 중앙 지층 글씨 제거
Debug.Log("========== C605 지층/암질 색띠 생성 ==========");
        Debug.Log("매립층 색띠 생성: " + fillCount);
        Debug.Log("퇴적층 색띠 생성: " + sedimentCount);
        Debug.Log("풍화토 색띠 생성: " + wsCount);
        Debug.Log("풍화암 색띠 생성: " + wrCount);
        Debug.Log("지층 글씨 생성: 매립층 / 퇴적층 / 풍화토 / 풍화암 / 굴착저면 EL(+29.54~31.00)");
        Debug.Log("도면 기준: C-610~C-619 문자에서 매립층, 퇴적층, 풍화토, 풍화암 및 시공하한선 EL 확인.");
        Debug.Log("==============================================");
    }

    private Material CreateSoilRockMaterial(Color color)
    {
        // 지층/암질 색띠 전용 반투명 재질
        Shader shader = GetWebSafeShader();
        Material mat = new Material(shader);

        mat.color = color;

        // Built-in Standard Shader 투명 설정
        mat.SetFloat("_Mode", 3f); // Transparent
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;

        return mat;
    }

    
    
    private int CreateSoilBandAlongPf(GameObject group, List<Vector3> centers, float topY, float bottomY, Material mat, string namePrefix)
    {
        if (group == null || centers == null || centers.Count < 2)
            return 0;

        Vector3 globalCenter = Vector3.zero;
        foreach (var c in centers)
            globalCenter += c;
        globalCenter /= centers.Count;

        float yTop = Mathf.Max(topY, bottomY);
        float yBottom = Mathf.Min(topY, bottomY);

        // 캡빔 안쪽에 자연스럽게 붙는 폭/위치
        float insideOffset = 0.75f;
        float bandWidth = 1.85f;

        List<Vector3> verts = new List<Vector3>();
        List<int> tris = new List<int>();

        int segmentCount = 0;

        for (int i = 0; i < centers.Count; i++)
        {
            Vector3 a = centers[i];
            Vector3 b = centers[(i + 1) % centers.Count];

            Vector3 dir = b - a;
            dir.y = 0f;

            float len = dir.magnitude;

            // 비정상 연결 제외
            if (len < 0.05f)
                continue;

            if (len > 12.0f)
                continue;

            dir.Normalize();

            Vector3 mid = (a + b) * 0.5f;
            Vector3 inward = globalCenter - mid;
            inward.y = 0f;

            if (inward.sqrMagnitude < 0.0001f)
                inward = Vector3.Cross(Vector3.up, dir);

            inward.Normalize();

            Vector3 aOuter = a + inward * insideOffset;
            Vector3 bOuter = b + inward * insideOffset;
            Vector3 aInner = a + inward * (insideOffset + bandWidth);
            Vector3 bInner = b + inward * (insideOffset + bandWidth);

            aOuter.y = yTop;
            bOuter.y = yTop;
            aInner.y = yTop;
            bInner.y = yTop;

            Vector3 aOuterBot = new Vector3(aOuter.x, yBottom, aOuter.z);
            Vector3 bOuterBot = new Vector3(bOuter.x, yBottom, bOuter.z);
            Vector3 aInnerBot = new Vector3(aInner.x, yBottom, aInner.z);
            Vector3 bInnerBot = new Vector3(bInner.x, yBottom, bInner.z);

            int v = verts.Count;

            // 0 top outer A
            // 1 top outer B
            // 2 top inner B
            // 3 top inner A
            // 4 bottom outer A
            // 5 bottom outer B
            // 6 bottom inner B
            // 7 bottom inner A
            verts.Add(aOuter);
            verts.Add(bOuter);
            verts.Add(bInner);
            verts.Add(aInner);
            verts.Add(aOuterBot);
            verts.Add(bOuterBot);
            verts.Add(bInnerBot);
            verts.Add(aInnerBot);

            // 상부면
            tris.Add(v + 0); tris.Add(v + 1); tris.Add(v + 2);
            tris.Add(v + 0); tris.Add(v + 2); tris.Add(v + 3);

            // 하부면
            tris.Add(v + 4); tris.Add(v + 6); tris.Add(v + 5);
            tris.Add(v + 4); tris.Add(v + 7); tris.Add(v + 6);

            // 외측 수직면
            tris.Add(v + 0); tris.Add(v + 4); tris.Add(v + 5);
            tris.Add(v + 0); tris.Add(v + 5); tris.Add(v + 1);

            // 내측 수직면
            tris.Add(v + 3); tris.Add(v + 2); tris.Add(v + 6);
            tris.Add(v + 3); tris.Add(v + 6); tris.Add(v + 7);

            // 시작 단면
            tris.Add(v + 0); tris.Add(v + 3); tris.Add(v + 7);
            tris.Add(v + 0); tris.Add(v + 7); tris.Add(v + 4);

            // 끝 단면
            tris.Add(v + 1); tris.Add(v + 5); tris.Add(v + 6);
            tris.Add(v + 1); tris.Add(v + 6); tris.Add(v + 2);

            segmentCount++;
        }

        if (verts.Count == 0)
            return 0;

        GameObject go = new GameObject(namePrefix + "_MESH_BAND");
        go.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.name = namePrefix + "_Mesh";
        mesh.SetVertices(verts);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = go.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = go.AddComponent<MeshRenderer>();
        mr.sharedMaterial = mat;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        mr.receiveShadows = false;

        Debug.Log("[SOIL_ROCK_LAYER] " + namePrefix + " 연속 Mesh 지층밴드 생성: " + segmentCount);

        return segmentCount;
    }



    private void CreateKoreanFloorLabel(GameObject group, string label, Vector3 position, float size, float plateWidth, float plateDepth)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_SOIL_TEXT_PLATE_" + label;
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.03f, position.z);
        plate.transform.localScale = new Vector3(plateWidth, 0.018f, plateDepth);

        Material plateMat = new Material(GetWebSafeShader());
        plateMat.color = Color.white;
        plate.GetComponent<Renderer>().material = plateMat;

        GameObject obj = new GameObject("C605_SOIL_TEXT_" + label);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = new Vector3(position.x, position.y + 0.06f, position.z);
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.085f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        Font font = KoreanFontProvider.Get();
        if (font == null)
            font = KoreanFontProvider.Get();

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = font.material;
                mr.material.color = Color.black;
            }
        }
    }


    private void CreateSoilRockLegendBoard(GameObject group, List<Vector3> centers, float bottomY)
    {
        if (centers == null || centers.Count == 0)
            return;

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minZ = float.MaxValue;
        float maxZ = float.MinValue;

        foreach (var p in centers)
        {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.z < minZ) minZ = p.z;
            if (p.z > maxZ) maxZ = p.z;
        }

        // 모델 내부 중앙이 아니라, 굴착장 외곽 한쪽에 범례를 배치
        Vector3 basePos = new Vector3(minX + 6.0f, bottomY + 0.65f, minZ - 5.5f);

        GameObject board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "C605_SOIL_ROCK_LEGEND_BOARD";
        board.transform.SetParent(group.transform, false);
        board.transform.position = new Vector3(basePos.x + 4.5f, basePos.y - 0.04f, basePos.z);
        board.transform.localScale = new Vector3(10.5f, 0.035f, 4.8f);

        Material boardMat = new Material(GetWebSafeShader());
        boardMat.color = new Color(1f, 1f, 1f, 0.92f);
        board.GetComponent<Renderer>().material = boardMat;

        Font font = KoreanFontProvider.Get();
        if (font == null)
            font = KoreanFontProvider.Get();

        CreateLegendTextLine(group, "지층 범례", new Vector3(basePos.x + 4.5f, basePos.y + 0.10f, basePos.z + 1.75f), 1.0f, font, "C605_LEGEND_TITLE");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.08f, basePos.z + 0.95f), new Color(0.45f, 0.25f, 0.08f, 0.85f), "BOX_매립층");
        CreateLegendTextLine(group, "매립층", new Vector3(basePos.x + 3.0f, basePos.y + 0.10f, basePos.z + 0.95f), 0.82f, font, "TXT_매립층");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.25f, basePos.z + 0.25f), new Color(0.78f, 0.55f, 0.22f, 0.85f), "BOX_퇴적층");
        CreateLegendTextLine(group, "퇴적층", new Vector3(basePos.x + 3.0f, basePos.y + 0.27f, basePos.z + 0.25f), 0.82f, font, "TXT_퇴적층");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.42f, basePos.z - 0.45f), new Color(0.95f, 0.72f, 0.18f, 0.90f), "BOX_풍화토");
        CreateLegendTextLine(group, "풍화토", new Vector3(basePos.x + 3.0f, basePos.y + 0.44f, basePos.z - 0.45f), 0.82f, font, "TXT_풍화토");

        CreateLegendColorBox(group, new Vector3(basePos.x + 1.0f, basePos.y + 0.59f, basePos.z - 1.15f), new Color(0.34f, 0.34f, 0.32f, 0.95f), "BOX_풍화암");
        CreateLegendTextLine(group, "풍화암", new Vector3(basePos.x + 3.0f, basePos.y + 0.61f, basePos.z - 1.15f), 0.82f, font, "TXT_풍화암");

        CreateLegendTextLine(group, "굴착저면  EL(+29.54~31.00)", new Vector3(basePos.x + 5.2f, basePos.y + 0.78f, basePos.z - 2.0f), 0.68f, font, "TXT_굴착저면EL");
    }

    private void CreateLegendColorBox(GameObject group, Vector3 position, Color color, string name)
    {
        GameObject box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = "C605_LEGEND_" + name;
        box.transform.SetParent(group.transform, false);
        box.transform.position = position;
        box.transform.localScale = new Vector3(1.1f, 0.05f, 0.38f);

        Material mat = new Material(GetWebSafeShader());
        mat.color = color;
        box.GetComponent<Renderer>().material = mat;
    }

    private void CreateLegendTextLine(GameObject group, string label, Vector3 position, float size, Font font, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = position;
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.08f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = font.material;
                mr.material.color = Color.black;
            }
        }
    }


    private void BuildSectionBottomElLabels(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("구간별 EL 글씨 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("SECTION_EL_TEXT");
        if (group == null)
        {
            group = new GameObject("SECTION_EL_TEXT");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("SECTION_EL_TEXT 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("구간별 EL 글씨 생성 실패: PF center 부족");
            return;
        }

        float bottomY = -7.65f;

        // C-612~C-619 굴착계획 전개도 PILE NO. 범위 + 시공하한선 기준
        // C-612 : P001~067        = EL(+30.44)
        // C-613 : P067~131        = EL(+30.44) / EL(+31.00)
        // C-614 : P131~196        = EL(+31.00)
        // C-615 : P196~248        = EL(+31.00)
        // C-616 : P248~306        = EL(+31.00) / EL(+29.54)
        // C-617 : P306~365        = EL(+31.00) / EL(+29.54) / 기반암층 상단
        // C-618 : P365~428        = EL(+31.00) / EL(+29.54)
        // C-619 : P428~492, P001  = EL(+31.00) / EL(+29.54)
        CreateSectionElLabelAtPfRange(group, centers, 1, 67, "P001~067  EL(+30.44)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 67, 131, "P067~131  EL(+30.44/31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 131, 196, "P131~196  EL(+31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 196, 248, "P196~248  EL(+31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 248, 306, "P248~306  EL(+31.00/29.54)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 306, 365, "P306~365  EL(+31.00/29.54/기반암)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 365, 428, "P365~428  EL(+31.00/29.54)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 428, 492, "P428~492  EL(+31.00/29.54)", bottomY);

        // 구간 EL 라벨은 검토용이므로 기본 OFF
        group.SetActive(false);

        Debug.Log("========== C605 구간별 굴착저면 EL 글씨 생성 ==========");
        Debug.Log("SECTION_EL_TEXT 생성 완료");
        Debug.Log("도면 기준: C-612~C-619 시공하한선 EL(+30.44), EL(+31.00), EL(+29.54), 기반암층 상단 반영.");
        Debug.Log("=====================================================");
    }

    private void CreateSectionElLabelAtPfRange(GameObject group, List<Vector3> centers, int startPf, int endPf, string label, float y)
    {
        if (centers == null || centers.Count == 0)
            return;

        int startIndex = Mathf.Clamp(startPf - 1, 0, centers.Count - 1);
        int endIndex = Mathf.Clamp(endPf - 1, 0, centers.Count - 1);

        Vector3 pos = (centers[startIndex] + centers[endIndex]) * 0.5f;

        // 벽체 바로 옆이 아니라 굴착 내부 쪽으로 조금 이동
        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        Vector3 inward = new Vector3(allCenter.x - pos.x, 0f, allCenter.z - pos.z);
        if (inward.sqrMagnitude > 0.0001f)
            inward.Normalize();

        pos += inward * 1.8f;
        pos.y = y + 0.20f;

        CreateSmallFloorTextPlate(group, label, pos, 0.30f, 4.2f, 0.55f);
    }

    private void CreateSmallFloorTextPlate(GameObject group, string label, Vector3 position, float size, float plateWidth, float plateDepth)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_SECTION_EL_PLATE_" + label;
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.03f, position.z);
        plate.transform.localScale = new Vector3(plateWidth, 0.018f, plateDepth);

        Material plateMat = new Material(GetWebSafeShader());
        plateMat.color = new Color(1f, 1f, 1f, 0.92f);
        plate.GetComponent<Renderer>().material = plateMat;

        GameObject obj = new GameObject("C605_SECTION_EL_TEXT_" + label);
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = new Vector3(position.x, position.y + 0.05f, position.z);
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.08f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.black;

        Font font = KoreanFontProvider.Get();
        if (font == null)
            font = KoreanFontProvider.Get();

        if (font != null)
        {
            tm.font = font;

            MeshRenderer mr = obj.GetComponent<MeshRenderer>();
            if (mr != null)
            {
                mr.material = font.material;
                mr.material.color = Color.black;
            }
        }
    }


    private void BuildPileSectionMarkers(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("PILE 구간 표시용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("PILE_SECTION_MARKER");
        if (group == null)
        {
            group = new GameObject("PILE_SECTION_MARKER");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("PILE_SECTION_MARKER 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("PILE 구간 표시 실패: PF center 부족");
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        // 전개도 기준 PILE NO 범위
        CreatePileSectionBoundary(group, centers, allCenter, 1, "P001", "C-612");
        CreatePileSectionBoundary(group, centers, allCenter, 67, "P067", "C-612/C-613");
        CreatePileSectionBoundary(group, centers, allCenter, 131, "P131", "C-613/C-614");
        CreatePileSectionBoundary(group, centers, allCenter, 196, "P196", "C-614/C-615");
        CreatePileSectionBoundary(group, centers, allCenter, 248, "P248", "C-615/C-616");
        CreatePileSectionBoundary(group, centers, allCenter, 306, "P306", "C-616/C-617");
        CreatePileSectionBoundary(group, centers, allCenter, 365, "P365", "C-617/C-618");
        CreatePileSectionBoundary(group, centers, allCenter, 428, "P428", "C-618/C-619");
        CreatePileSectionBoundary(group, centers, allCenter, 492, "P492", "C-619");
        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김

        // PILE 구간명 라벨은 구간EL과 겹쳐서 숨김
Debug.Log("========== C605 PILE 구간 경계/라벨 생성 ==========");
        Debug.Log("PILE_SECTION_MARKER 생성 완료: C-612~C-619 PILE NO 범위");
        Debug.Log("도면 기준: C-612 P001~067, C-613 P067~131, C-614 P131~196, C-615 P196~248, C-616 P248~306, C-617 P306~365, C-618 P365~428, C-619 P428~492");
        Debug.Log("=================================================");
    }

    private void CreatePileSectionBoundary(GameObject group, List<Vector3> centers, Vector3 allCenter, int pfNo, string label, string sheet)
    {
        int index = Mathf.Clamp(pfNo - 1, 0, centers.Count - 1);

        Vector3 p = centers[index];

        Vector3 inward = new Vector3(allCenter.x - p.x, 0f, allCenter.z - p.z);
        if (inward.sqrMagnitude > 0.0001f)
            inward.Normalize();

        Vector3 basePos = p + inward * 1.0f;

        float topY = -1.0f;
        float bottomY = -7.2f;

        Vector3 a = new Vector3(basePos.x, topY, basePos.z);
        Vector3 b = new Vector3(basePos.x, bottomY, basePos.z);

        GameObject marker = GameObject.CreatePrimitive(PrimitiveType.Cube);
        marker.name = "C605_PILE_SECTION_BOUNDARY_" + label;
        marker.transform.SetParent(group.transform, false);
        marker.transform.position = (a + b) * 0.5f;
        marker.transform.localScale = new Vector3(0.035f, Mathf.Abs(topY - bottomY), 0.035f);

        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(0.85f, 0.85f, 0.85f, 0.28f);
        marker.GetComponent<Renderer>().material = mat;

        Vector3 textPos = p + inward * 1.15f;
        textPos.y = -0.55f;

        CreatePileMarkerText(group, label, textPos, 0.18f, 0.9f, 0.32f);
    }

    private void CreatePileSectionRangeLabel(GameObject group, List<Vector3> centers, Vector3 allCenter, int startPf, int endPf, string label)
    {
        int startIndex = Mathf.Clamp(startPf - 1, 0, centers.Count - 1);
        int endIndex = Mathf.Clamp(endPf - 1, 0, centers.Count - 1);

        Vector3 p = (centers[startIndex] + centers[endIndex]) * 0.5f;

        Vector3 inward = new Vector3(allCenter.x - p.x, 0f, allCenter.z - p.z);
        if (inward.sqrMagnitude > 0.0001f)
            inward.Normalize();

        Vector3 textPos = p + inward * 3.5f;
        textPos.y = 1.15f;

        CreatePileMarkerText(group, label, textPos, 0.38f, 4.8f, 0.75f);
    }

    private void CreatePileMarkerText(GameObject group, string label, Vector3 position, float size, float plateWidth, float plateDepth)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_PILE_MARKER_PLATE_" + label.Replace("\n", "_");
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.03f, position.z);
        plate.transform.localScale = new Vector3(plateWidth, 0.018f, plateDepth);

        Material plateMat = new Material(GetWebSafeShader());
        plateMat.color = new Color(0f, 0f, 0f, 0.32f);
        plate.GetComponent<Renderer>().material = plateMat;

        GameObject obj = new GameObject("C605_PILE_MARKER_TEXT_" + label.Replace("\n", "_"));
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = new Vector3(position.x, position.y + 0.05f, position.z);
        obj.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        TextMesh tm = obj.AddComponent<TextMesh>();
        tm.text = label;
        tm.fontSize = 96;
        tm.characterSize = size * 0.08f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = Color.white;

        Font font = KoreanFontProvider.Get();
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
    }


    private void BuildBottomZoneLines(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("바닥 구간선 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("BOTTOM_ZONE_LINE");
        if (group == null)
        {
            group = new GameObject("BOTTOM_ZONE_LINE");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("BOTTOM_ZONE_LINE 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("바닥 구간선 생성 실패: PF center 부족");
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        float y = -7.42f;

        // C-612~C-619 PILE NO 경계 기준
        CreateBottomZoneLine(group, centers, allCenter, 67, y);
        CreateBottomZoneLine(group, centers, allCenter, 131, y);
        CreateBottomZoneLine(group, centers, allCenter, 196, y);
        CreateBottomZoneLine(group, centers, allCenter, 248, y);
        CreateBottomZoneLine(group, centers, allCenter, 306, y);
        CreateBottomZoneLine(group, centers, allCenter, 365, y);
        CreateBottomZoneLine(group, centers, allCenter, 428, y);

        // 바닥 구간선은 검토용이므로 기본 OFF
        group.SetActive(false);

        Debug.Log("========== C605 바닥 EL 구간선 생성 ==========");
        Debug.Log("BOTTOM_ZONE_LINE 생성 완료: P067/P131/P196/P248/P306/P365/P428");
        Debug.Log("기본 OFF: 필요 시 버튼으로 표시");
        Debug.Log("============================================");
    }

    private void CreateBottomZoneLine(GameObject group, List<Vector3> centers, Vector3 allCenter, int pfNo, float y)
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

        Material mat = new Material(GetWebSafeShader());
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

        Font font = KoreanFontProvider.Get();
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
    }


    private void BuildBottomElZones(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("바닥 EL 구역 생성용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("BOTTOM_EL_ZONE");
        if (group == null)
        {
            group = new GameObject("BOTTOM_EL_ZONE");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("BOTTOM_EL_ZONE 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("바닥 EL 구역 생성 실패: PF center 부족");
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        float y = -7.36f;
        float zoneWidth = 5.8f;

        Material el3044 = CreateBottomElZoneMaterial(new Color(0.45f, 0.70f, 0.95f, 0.38f)); // EL 30.44
        Material el3100 = CreateBottomElZoneMaterial(new Color(0.45f, 0.85f, 0.60f, 0.35f)); // EL 31.00
        Material el2954 = CreateBottomElZoneMaterial(new Color(0.25f, 0.42f, 0.75f, 0.45f)); // EL 29.54
        Material bedrock = CreateBottomElZoneMaterial(new Color(0.25f, 0.25f, 0.25f, 0.50f)); // 기반암층 상단
        Material mixed = CreateBottomElZoneMaterial(new Color(0.80f, 0.80f, 0.80f, 0.30f));   // 복합구간

        // 도면 기준:
        // C-612 P001~067 = EL(+30.44)
        // C-613 P067~131 = EL(+30.44) / EL(+31.00)
        // C-614 P131~196 = EL(+31.00)
        // C-615 P196~248 = EL(+31.00)
        // C-616 P248~306 = EL(+31.00) / EL(+29.54)
        // C-617 P306~365 = EL(+31.00) / EL(+29.54) / 기반암층 상단
        // C-618 P365~428 = EL(+31.00) / EL(+29.54)
        // C-619 P428~492 = EL(+31.00) / EL(+29.54)
        int c1 = CreateBottomElZoneByPfRange(group, centers, allCenter, 1, 67, y, zoneWidth, el3044, "EL3044");
        int c2 = CreateBottomElZoneByPfRange(group, centers, allCenter, 67, 131, y, zoneWidth, mixed, "EL3044_3100");
        int c3 = CreateBottomElZoneByPfRange(group, centers, allCenter, 131, 248, y, zoneWidth, el3100, "EL3100");
        int c4 = CreateBottomElZoneByPfRange(group, centers, allCenter, 248, 306, y, zoneWidth, mixed, "EL3100_2954");
        int c5 = CreateBottomElZoneByPfRange(group, centers, allCenter, 306, 365, y, zoneWidth, bedrock, "BEDROCK_TOP");
        int c6 = CreateBottomElZoneByPfRange(group, centers, allCenter, 365, 492, y, zoneWidth, el2954, "EL2954");

        // EL구역 큰 면은 검토용이므로 기본 OFF
        group.SetActive(false);

        Debug.Log("========== C605 바닥 EL 구역 색상 생성 ==========");
        Debug.Log("EL(+30.44) 구역 생성: " + c1);
        Debug.Log("EL(+30.44/31.00) 복합 구역 생성: " + c2);
        Debug.Log("EL(+31.00) 구역 생성: " + c3);
        Debug.Log("EL(+31.00/29.54) 복합 구역 생성: " + c4);
        Debug.Log("기반암층 상단 구역 생성: " + c5);
        Debug.Log("EL(+29.54) 구역 생성: " + c6);
        Debug.Log("도면 기준: C-612~C-619 PILE NO 범위와 시공하한선 EL 반영.");
        Debug.Log("==============================================");
    }

    private Material CreateBottomElZoneMaterial(Color color)
    {
        Shader shader = GetWebSafeShader();
        Material mat = new Material(shader);

        mat.color = color;
        mat.SetFloat("_Mode", 3f);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;

        return mat;
    }

    private int CreateBottomElZoneByPfRange(GameObject group, List<Vector3> centers, Vector3 allCenter, int startPf, int endPf, float y, float width, Material mat, string label)
    {
        if (centers == null || centers.Count < 2)
            return 0;

        int startIndex = Mathf.Clamp(startPf - 1, 0, centers.Count - 1);
        int endIndex = Mathf.Clamp(endPf - 1, 0, centers.Count - 1);

        int created = 0;

        for (int i = startIndex; i < endIndex && i < centers.Count - 1; i++)
        {
            Vector3 c0 = centers[i];
            Vector3 c1 = centers[i + 1];

            float d = Vector3.Distance(c0, c1);
            if (d < 0.05f || d > 20f)
                continue;

            Vector3 mid = (c0 + c1) * 0.5f;
            Vector3 inward = new Vector3(allCenter.x - mid.x, 0f, allCenter.z - mid.z);
            if (inward.sqrMagnitude > 0.0001f)
                inward.Normalize();
            else
                inward = Vector3.zero;

            Vector3 p0 = new Vector3(c0.x, y, c0.z) + inward * 0.65f;
            Vector3 p1 = new Vector3(c1.x, y, c1.z) + inward * 0.65f;
            Vector3 p2 = new Vector3(c1.x, y, c1.z) + inward * width;
            Vector3 p3 = new Vector3(c0.x, y, c0.z) + inward * width;

            GameObject obj = new GameObject("C605_BOTTOM_EL_ZONE_" + label + "_" + created);
            obj.transform.SetParent(group.transform, false);

            Mesh mesh = new Mesh();
            mesh.vertices = new Vector3[] { p0, p1, p2, p3 };
            mesh.triangles = new int[] { 0, 1, 2, 0, 2, 3 };
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();

            MeshFilter mf = obj.AddComponent<MeshFilter>();
            mf.sharedMesh = mesh;

            MeshRenderer mr = obj.AddComponent<MeshRenderer>();
            mr.material = mat;

            created++;
        }

        return created;
    }


    private void BuildC605PlanOverlay(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogError("도면 오버레이용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("PLAN_OVERLAY");
        if (group == null)
        {
            group = new GameObject("PLAN_OVERLAY");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("PLAN_OVERLAY 그룹이 없어 강제 생성했습니다.");
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 3)
        {
            Debug.LogWarning("도면 오버레이 생성 실패: PF center 부족");
            return;
        }

        float minX = float.MaxValue;
        float maxX = float.MinValue;
        float minZ = float.MaxValue;
        float maxZ = float.MinValue;

        foreach (var p in centers)
        {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.z < minZ) minZ = p.z;
            if (p.z > maxZ) maxZ = p.z;
        }

        float padX = (maxX - minX) * 0.035f;
        float padZ = (maxZ - minZ) * 0.035f;

        minX -= padX;
        maxX += padX;
        minZ -= padZ;
        maxZ += padZ;

        string imgPath = Path.Combine(Application.streamingAssetsPath, "WangsukDXF", "Overlay", "c605_plan_overlay_visible.png");

        if (!File.Exists(imgPath))
        {
            Debug.LogWarning("도면 오버레이 PNG 없음: " + imgPath);
            return;
        }

        byte[] bytes = File.ReadAllBytes(imgPath);
        Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        tex.LoadImage(bytes);
        tex.wrapMode = TextureWrapMode.Clamp;
        tex.filterMode = FilterMode.Bilinear;

        Material mat = new Material(GetWebSafeTransparentShader());
        if (mat.shader == null)
            mat = new Material(GetWebSafeShader());

        mat.mainTexture = tex;
        mat.color = new Color(1f, 1f, 1f, 1.0f);
        mat.renderQueue = 3100;

        float y = -6.95f;

        Vector3 v0 = new Vector3(minX, y, minZ);
        Vector3 v1 = new Vector3(maxX, y, minZ);
        Vector3 v2 = new Vector3(maxX, y, maxZ);
        Vector3 v3 = new Vector3(minX, y, maxZ);

        GameObject obj = new GameObject("C605_PLAN_OVERLAY_TEXTURE");
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = new Vector3[] { v0, v1, v2, v3 };
        mesh.triangles = new int[] { 0, 2, 1, 0, 3, 2 };

        // 필요 시 뒤집힘 보정은 여기 UV 순서만 바꾸면 됨
        mesh.uv = new Vector2[]
        {
            new Vector2(0f, 0f),
            new Vector2(1f, 0f),
            new Vector2(1f, 1f),
            new Vector2(0f, 1f)
        };

        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;

        // 기본은 OFF. 필요할 때 도면 버튼으로 켠다.
        group.SetActive(false);

        Debug.Log("========== C605 평면도 도면 오버레이 생성 ==========");
        Debug.Log("PLAN_OVERLAY 생성 완료: " + imgPath);
        Debug.Log("기준: C-605 PF/H-PILE bbox와 동일 정규화 좌표에 투명 PNG 배치.");
        Debug.Log("기본 OFF: 도면 버튼으로 표시");
        Debug.Log("===============================================");
    }


    private void BuildDongjariVectorOverlay(string jsonFileName)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(jsonFileName);
        if (data == null || data.entities == null)
        {
            Debug.LogWarning("동자리 벡터 오버레이 JSON 없음: " + jsonFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("PLAN_VECTOR_OVERLAY");
        if (group == null)
        {
            group = new GameObject("PLAN_VECTOR_OVERLAY");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("PLAN_VECTOR_OVERLAY 그룹이 없어 강제 생성했습니다.");
        }

        Material mat = new Material(Shader.Find("Sprites/Default"));
        mat.color = new Color(1f, 1f, 1f, 0.88f);

        int created = 0;
        float y = -6.18f;

        foreach (var e in data.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(e, y);

            if (pts == null || pts.Count < 2)
                continue;

            for (int i = 0; i < pts.Count - 1; i++)
            {
                Vector3 a = pts[i];
                Vector3 b = pts[i + 1];

                float len = Vector3.Distance(a, b);

                if (len < 0.03f || len > 60f)
                    continue;

                CreateDongjariLine(group, a, b, mat, "DONGJARI_LINE_" + created);
                created++;
            }
        }

        // 기본 OFF. 버튼으로 필요할 때 표시.
        group.SetActive(false);

        Debug.Log("========== C605 동자리/건물선 바닥 오버레이 생성 ==========");
        Debug.Log("PLAN_VECTOR_OVERLAY 생성: " + created);
        Debug.Log("어스앙카/띠장/버팀/PF 반복심볼 제외 후 바닥용 선만 표시.");
        Debug.Log("기본 OFF: 동자리 버튼으로 표시");
        Debug.Log("========================================================");
    }

    private void CreateDongjariLine(GameObject group, Vector3 a, Vector3 b, Material mat, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        LineRenderer lr = obj.AddComponent<LineRenderer>();
        lr.useWorldSpace = false;
        lr.positionCount = 2;
        lr.SetPosition(0, a);
        lr.SetPosition(1, b);
        lr.startWidth = 0.055f;
        lr.endWidth = 0.055f;
        lr.material = mat;
        lr.numCapVertices = 0;
        lr.numCornerVertices = 0;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        lr.receiveShadows = false;
    }


    private void BuildFinalBottomStepFromDongjari(string jsonFileName)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(jsonFileName);
        if (data == null || data.entities == null)
        {
            Debug.LogWarning("최종바닥 단차용 동자리 JSON 없음: " + jsonFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("FINAL_BOTTOM_STEP");
        if (group == null)
        {
            group = new GameObject("FINAL_BOTTOM_STEP");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("FINAL_BOTTOM_STEP 그룹이 없어 강제 생성했습니다.");
        }

        Material topLineMat = new Material(Shader.Find("Sprites/Default"));
        topLineMat.color = new Color(0.25f, 0.95f, 1f, 0.95f);

        Material lowerLineMat = new Material(Shader.Find("Sprites/Default"));
        lowerLineMat.color = new Color(0.05f, 0.35f, 1f, 0.85f);

        Material wallMat = new Material(GetWebSafeShader());
        wallMat.color = new Color(0.1f, 0.45f, 0.9f, 0.28f);
        wallMat.SetFloat("_Mode", 3f);
        wallMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        wallMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        wallMat.SetInt("_ZWrite", 0);
        wallMat.DisableKeyword("_ALPHATEST_ON");
        wallMat.EnableKeyword("_ALPHABLEND_ON");
        wallMat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        wallMat.renderQueue = 3100;

        // 현재 모델 기준:
        // 기존 바닥 위쪽 표시선, 추가 굴착 후보 하부선
        // 실제 깊이는 기초평면/단면도 확인 후 수정.
        float topY = -6.12f;
        float lowerY = -7.05f;

        int created = 0;
        int wallCreated = 0;

        foreach (var e in data.entities)
        {
            List<Vector3> rawPts = ConvertEntityPoints(e, 0f);

            if (rawPts == null || rawPts.Count < 2)
                continue;

            for (int i = 0; i < rawPts.Count - 1; i++)
            {
                Vector3 p0 = rawPts[i];
                Vector3 p1 = rawPts[i + 1];

                float len = Vector3.Distance(p0, p1);

                // 너무 짧은 해치/심볼성 조각과 너무 긴 기준선 제외
                if (len < 0.35f || len > 28f)
                    continue;

                Vector3 aTop = new Vector3(p0.x, topY, p0.z);
                Vector3 bTop = new Vector3(p1.x, topY, p1.z);
                Vector3 aLow = new Vector3(p0.x, lowerY, p0.z);
                Vector3 bLow = new Vector3(p1.x, lowerY, p1.z);

                CreateFinalBottomStepLine(group, aTop, bTop, topLineMat, "FINAL_STEP_TOP_" + created, 0.045f);
                CreateFinalBottomStepLine(group, aLow, bLow, lowerLineMat, "FINAL_STEP_LOW_" + created, 0.035f);

                // 모든 선에 벽면을 만들면 과해지므로 일정 간격으로만 수직 단차면 생성
                if (created % 3 == 0)
                {
                    CreateFinalBottomStepWall(group, aTop, bTop, bLow, aLow, wallMat, "FINAL_STEP_WALL_" + wallCreated);
                    wallCreated++;
                }

                created++;
            }
        }

        // 기본 OFF. 검토할 때 최종바닥 버튼으로 표시.
        group.SetActive(false);

        Debug.Log("========== C605 최종바닥 단차 후보 생성 ==========");
        Debug.Log("FINAL_BOTTOM_STEP 라인 생성: " + created);
        Debug.Log("FINAL_BOTTOM_STEP 단차면 생성: " + wallCreated);
        Debug.Log("동자리/건물선 기준 검토용. 실제 깊이는 기초도면 EL 확인 후 보정 필요.");
        Debug.Log("기본 OFF: 최종바닥 버튼으로 표시");
        Debug.Log("===============================================");
    }

    private void CreateFinalBottomStepLine(GameObject group, Vector3 a, Vector3 b, Material mat, string name, float width)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        LineRenderer lr = obj.AddComponent<LineRenderer>();
        lr.useWorldSpace = false;
        lr.positionCount = 2;
        lr.SetPosition(0, a);
        lr.SetPosition(1, b);
        lr.startWidth = width;
        lr.endWidth = width;
        lr.material = mat;
        lr.numCapVertices = 0;
        lr.numCornerVertices = 0;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        lr.receiveShadows = false;
    }

    private void CreateFinalBottomStepWall(GameObject group, Vector3 aTop, Vector3 bTop, Vector3 bLow, Vector3 aLow, Material mat, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = new Vector3[] { aTop, bTop, bLow, aLow };
        mesh.triangles = new int[] { 0, 1, 2, 0, 2, 3 };
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;
    }


    private void BuildForceWaleLevel4FromPfCenters(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogWarning("4단 띠장 보강용 PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        // 기존 띠장 버튼과 같이 켜지고 꺼지도록 WALE 그룹에 붙임
        GameObject group = registry.GetGroup("WALE");
        if (group == null)
        {
            group = GameObject.Find("WALE");
            if (group == null)
            {
                group = new GameObject("WALE");
                group.transform.SetParent(root.transform, false);
                Debug.LogWarning("WALE 그룹이 없어 강제 생성했습니다.");
            }
        }

        // 중복 생성 방지
        for (int i = group.transform.childCount - 1; i >= 0; i--)
        {
            Transform child = group.transform.GetChild(i);
            if (child != null && child.name.StartsWith("C605_FORCE_WALE_L4_"))
                DestroyImmediate(child.gameObject);
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 10)
        {
            Debug.LogWarning("4단 띠장 보강 실패: PF center 부족");
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        Material mat = new Material(GetWebSafeShader());
        mat.color = new Color(1.0f, 0.72f, 0.05f, 1f);

        int created = 0;

        // C-616 P248~306, C-617 P306~365, C-618 P365~428은 4단 후보 반영
        // index는 0부터 시작하므로 P248 = 247
        int startPf = 248;
        int endPf = 428;

        for (int pfNo = startPf; pfNo < endPf; pfNo++)
        {
            int i0 = Mathf.Clamp(pfNo - 1, 0, centers.Count - 1);
            int i1 = Mathf.Clamp(pfNo, 0, centers.Count - 1);

            Vector3 p0 = centers[i0];
            Vector3 p1 = centers[i1];

            float dist = Vector3.Distance(p0, p1);
            if (dist < 0.05f || dist > 12f)
                continue;

            Vector3 mid = (p0 + p1) * 0.5f;
            Vector3 inward = new Vector3(allCenter.x - mid.x, 0f, allCenter.z - mid.z);
            if (inward.sqrMagnitude > 0.0001f)
                inward.Normalize();

            // 기존 벽면 안쪽에 붙이기 위한 소폭 offset
            Vector3 a = new Vector3(p0.x, -waleDepth4, p0.z) + inward * 0.32f;
            Vector3 b = new Vector3(p1.x, -waleDepth4, p1.z) + inward * 0.32f;

            CreateForceWaleL4Segment(group, a, b, mat, "C605_FORCE_WALE_L4_P" + pfNo.ToString("000"));
            created++;
        }

        Debug.Log("========== C605 4단 띠장 강제 보강 ==========");
        Debug.Log("FORCE WALE L4 생성 구간: P248~P428");
        Debug.Log("FORCE WALE L4 생성 수: " + created);
        Debug.Log("도면 검토 기준: C-616~C-618 4단 후보 반영. 실제 EL은 추후 보정.");
        Debug.Log("===========================================");
    }

    private void CreateForceWaleL4Segment(GameObject group, Vector3 a, Vector3 b, Material mat, string name)
    {
        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.05f)
            return;

        GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Cube);
        obj.name = name;
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = (a + b) * 0.5f;
        obj.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        // 띠장 H형강처럼 보이도록 길이방향 큐브
        obj.transform.localScale = new Vector3(0.34f, 0.24f, len);

        Renderer r = obj.GetComponent<Renderer>();
        if (r != null)
            r.material = mat;
    }


    private Material CreateWaleSpecTransparentMaterial(Color color)
    {
        Shader shader = Shader.Find("Universal Render Pipeline/Lit");
        if (shader == null)
            shader = GetWebSafeShader();

        Material mat = new Material(shader);
        mat.color = color;

        if (mat.HasProperty("_BaseColor"))
            mat.SetColor("_BaseColor", color);

        if (mat.HasProperty("_Surface"))
            mat.SetFloat("_Surface", 1f);

        if (mat.HasProperty("_Blend"))
            mat.SetFloat("_Blend", 0f);

        if (mat.HasProperty("_SrcBlend"))
            mat.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);

        if (mat.HasProperty("_DstBlend"))
            mat.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);

        if (mat.HasProperty("_ZWrite"))
            mat.SetFloat("_ZWrite", 0f);

        mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;

        return mat;
    }

    private Material CreateWaleSpecOpaqueMaterial(Color color)
    {
        Shader shader = Shader.Find("Universal Render Pipeline/Lit");
        if (shader == null)
            shader = GetWebSafeShader();

        Material mat = new Material(shader);
        mat.color = color;

        if (mat.HasProperty("_BaseColor"))
            mat.SetColor("_BaseColor", color);

        if (mat.HasProperty("_Surface"))
            mat.SetFloat("_Surface", 0f);

        if (mat.HasProperty("_ZWrite"))
            mat.SetFloat("_ZWrite", 1f);

        mat.renderQueue = -1;
        return mat;
    }
    private class WaleSpecRange
    {
        public int startPf;
        public int endPf;
        public int bandIndex;
        public bool doubleH;
        public string source;

        public WaleSpecRange(int startPf, int endPf, int bandIndex, bool doubleH, string source)
        {
            this.startPf = startPf;
            this.endPf = endPf;
            this.bandIndex = bandIndex;
            this.doubleH = doubleH;
            this.source = source;
        }
    }

    private void BuildWaleSpecReviewFromPfCenters(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogWarning("WALE_SPEC_REVIEW PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = GameObject.Find("WALE_SPEC_REVIEW");
        if (group == null)
        {
            group = new GameObject("WALE_SPEC_REVIEW");
            group.transform.SetParent(root.transform, false);
        }

        for (int i = group.transform.childCount - 1; i >= 0; i--)
        {
            Transform child = group.transform.GetChild(i);
            if (child != null)
                DestroyImmediate(child.gameObject);
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 400)
        {
            Debug.LogWarning("WALE_SPEC_REVIEW PF center 부족: " + centers.Count);
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        Material matSingle = CreateWaleSpecTransparentMaterial(new Color(0.72f, 0.45f, 1.00f, 0.26f));
        Material matDouble = CreateWaleSpecTransparentMaterial(new Color(0.72f, 0.45f, 1.00f, 0.26f));
        Material matOutline = CreateWaleSpecOpaqueMaterial(new Color(0.30f, 0.00f, 0.65f, 1.00f));
List<WaleSpecRange> specs = GetWaleSpecReviewRanges();

        int created = 0;

        foreach (var spec in specs)
        {
            created += CreateWaleSpecRange(group, centers, allCenter, spec, matSingle, matDouble, matOutline);
        }

        GameObject oldWale = GameObject.Find("WALE");
        if (oldWale != null)
        {
            oldWale.SetActive(false);
            Debug.Log("기존 WALE 노란 띠장 자동 숨김 처리");
        }
        HideLegacyWaleObjectsExceptSpecReview();
        Debug.Log("========== WALE_SPEC_REVIEW 도면기준 띠장 생성 ==========");
        Debug.Log("기준: C-612~C-619 WALE Spec Review v1");
        Debug.Log("생성 부재 수: " + created);
        Debug.Log("주의: 기존 WALE과 비교하기 위한 검토용 그룹입니다.");
        Debug.Log("색상: 보라 반투명=도면기준 띠장, 진보라=외곽선");
        Debug.Log("======================================================");
    }

    private List<WaleSpecRange> GetWaleSpecReviewRanges()
    {
        List<WaleSpecRange> list = new List<WaleSpecRange>();

        // C-612 / P001~P067 : 2단
        list.Add(new WaleSpecRange(1, 67, 1, true, "C-612 BAND1"));
        list.Add(new WaleSpecRange(1, 67, 2, true, "C-612 BAND2"));

        // C-613 / P067~P131 : 기본 2단 + P095~P116 부분 3단
        list.Add(new WaleSpecRange(67, 131, 1, true, "C-613 BAND1"));
        list.Add(new WaleSpecRange(67, 131, 2, true, "C-613 BAND2"));
        list.Add(new WaleSpecRange(95, 116, 3, true, "C-613 BAND3"));

        // C-614 / P131~P196 : 기본 2단 + P178~P196 부분 3단
        list.Add(new WaleSpecRange(131, 196, 1, true, "C-614 BAND1"));
        list.Add(new WaleSpecRange(131, 196, 2, true, "C-614 BAND2"));
        list.Add(new WaleSpecRange(178, 196, 3, true, "C-614 BAND3"));

        // C-615 / P196~P248 : 전 구간 3단
        list.Add(new WaleSpecRange(196, 248, 1, true, "C-615 BAND1"));
        list.Add(new WaleSpecRange(196, 248, 2, true, "C-615 BAND2"));
        list.Add(new WaleSpecRange(196, 248, 3, true, "C-615 BAND3"));

        // C-616 / P248~P306 : 기본 2단 + 부분 3단/4단
        list.Add(new WaleSpecRange(248, 306, 1, true, "C-616 BAND1"));
        list.Add(new WaleSpecRange(248, 306, 2, true, "C-616 BAND2"));
        list.Add(new WaleSpecRange(248, 258, 3, true, "C-616 BAND3_A"));
        list.Add(new WaleSpecRange(278, 306, 3, true, "C-616 BAND3_B"));
        list.Add(new WaleSpecRange(248, 251, 4, true, "C-616 BAND4_A"));
        list.Add(new WaleSpecRange(280, 306, 4, true, "C-616 BAND4_B"));

        // C-617 / P306~P365 : 4단 후보
        list.Add(new WaleSpecRange(306, 347, 1, true, "C-617 BAND1"));
        list.Add(new WaleSpecRange(306, 364, 2, true, "C-617 BAND2_P365_CORNER_SKIP"));
        list.Add(new WaleSpecRange(306, 364, 3, true, "C-617 BAND3_P365_CORNER_SKIP"));
        list.Add(new WaleSpecRange(306, 364, 4, true, "C-617 BAND4_P365_CORNER_SKIP"));

        // C-618 / P365~P428 : 복합 4단
        list.Add(new WaleSpecRange(367, 405, 1, true, "C-618 BAND1_P365_CORNER_SKIP"));
        list.Add(new WaleSpecRange(367, 428, 2, true, "C-618 BAND2_P365_CORNER_SKIP"));
        list.Add(new WaleSpecRange(367, 428, 3, true, "C-618 BAND3_P365_CORNER_SKIP"));
        list.Add(new WaleSpecRange(405, 428, 4, true, "C-618 BAND4"));

        // C-619 / P428~P492,P001 : 복합 3단
        list.Add(new WaleSpecRange(428, 475, 1, true, "C-619 BAND1_A"));
        list.Add(new WaleSpecRange(483, 492, 1, true, "C-619 BAND1_B"));
        list.Add(new WaleSpecRange(1, 2, 1, true, "C-619 BAND1_C"));

        list.Add(new WaleSpecRange(428, 475, 2, true, "C-619 BAND2_A"));
        list.Add(new WaleSpecRange(486, 492, 2, true, "C-619 BAND2_B"));
        list.Add(new WaleSpecRange(1, 2, 2, true, "C-619 BAND2_C"));

        list.Add(new WaleSpecRange(428, 469, 3, true, "C-619 BAND3"));

        return list;
    }

    private float GetWaleSpecDepthByBand(int bandIndex)
    {
        // 검토용 깊이값.
        // 최종은 바닥 EL(+30.44/+31.00/+29.54)와 단면도 대조 후 보정.
        if (bandIndex <= 1)
            return 1.0f;

        if (bandIndex == 2)
            return 3.0f;

        if (bandIndex == 3)
            return 4.8f;

        return 6.0f;
    }

    private int CreateWaleSpecRange(GameObject group, List<Vector3> centers, Vector3 allCenter, WaleSpecRange spec, Material matSingle, Material matDouble, Material matOutline)
    {
        int created = 0;

        int startPf = Mathf.Clamp(spec.startPf, 1, centers.Count);
        int endPf = Mathf.Clamp(spec.endPf, 1, centers.Count);

        if (endPf <= startPf)
            return 0;

        float depth = GetWaleSpecDepthByBand(spec.bandIndex);

        for (int pfNo = startPf; pfNo < endPf; pfNo++)
        {
            int i0 = Mathf.Clamp(pfNo - 1, 0, centers.Count - 1);
            int i1 = Mathf.Clamp(pfNo, 0, centers.Count - 1);

            Vector3 p0 = centers[i0];
            Vector3 p1 = centers[i1];

            float dist = Vector3.Distance(p0, p1);
            if (dist < 0.03f || dist > 12f)
                continue;

            Vector3 mid = (p0 + p1) * 0.5f;
            Vector3 inward = new Vector3(allCenter.x - mid.x, 0f, allCenter.z - mid.z);

            if (inward.sqrMagnitude > 0.0001f)
                inward.Normalize();
            else
                inward = Vector3.forward;

            string baseName = "WALE_SPEC_" + spec.source + "_P" + pfNo.ToString("000") + "_B" + spec.bandIndex;

            if (spec.doubleH)
            {

                CreateWaleSpecBeam(group, p0, p1, Mathf.Max(0.05f, depth - 0.15f), inward * 0.42f, matDouble, matOutline, baseName + "_2H_UPPER");
                CreateWaleSpecBeam(group, p0, p1, depth + 0.15f, inward * 0.42f, matDouble, matOutline, baseName + "_2H_LOWER");
                created += 2;
            }
            else
            {
                Vector3 offset = inward * 0.42f;
                CreateWaleSpecBeam(group, p0, p1, depth, offset, matSingle, matOutline, baseName + "_H");
                created += 1;
            }
        }

        return created;
    }

    private void CreateWaleSpecBeam(GameObject group, Vector3 p0, Vector3 p1, float depth, Vector3 offset, Material mat, Material outlineMat, string name)
    {
        Vector3 a = new Vector3(p0.x, -depth, p0.z) + offset;
        Vector3 b = new Vector3(p1.x, -depth, p1.z) + offset;

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.03f)
            return;

        Transform existing = group.transform.Find(name);
        if (existing != null)
            return;

        GameObject root = new GameObject(name);
        root.transform.SetParent(group.transform, false);
        root.transform.position = (a + b) * 0.5f;
        root.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        float beamWidth = 0.22f;
        float beamHeight = 0.18f;
        float edge = 0.035f;

        // 내부 채움: 보라색 반투명
        GameObject fill = GameObject.CreatePrimitive(PrimitiveType.Cube);
        fill.name = name + "_FILL_TRANSPARENT";
        fill.transform.SetParent(root.transform, false);
        fill.transform.localPosition = Vector3.zero;
        fill.transform.localRotation = Quaternion.identity;
        fill.transform.localScale = new Vector3(beamWidth, beamHeight, len);

        Renderer fillRenderer = fill.GetComponent<Renderer>();
        if (fillRenderer != null)
            fillRenderer.material = mat;

        // 외곽선: 진보라 불투명, 긴 방향 4개 모서리선
        CreateWaleSpecEdge(root.transform, new Vector3( beamWidth * 0.5f,  beamHeight * 0.5f, 0f), edge, len, outlineMat, name + "_EDGE_RT");
        CreateWaleSpecEdge(root.transform, new Vector3(-beamWidth * 0.5f,  beamHeight * 0.5f, 0f), edge, len, outlineMat, name + "_EDGE_LT");
        CreateWaleSpecEdge(root.transform, new Vector3( beamWidth * 0.5f, -beamHeight * 0.5f, 0f), edge, len, outlineMat, name + "_EDGE_RB");
        CreateWaleSpecEdge(root.transform, new Vector3(-beamWidth * 0.5f, -beamHeight * 0.5f, 0f), edge, len, outlineMat, name + "_EDGE_LB");
    }

    private void CreateWaleSpecEdge(Transform parent, Vector3 localPos, float edge, float len, Material outlineMat, string name)
    {
        GameObject e = GameObject.CreatePrimitive(PrimitiveType.Cube);
        e.name = name;
        e.transform.SetParent(parent, false);
        e.transform.localPosition = localPos;
        e.transform.localRotation = Quaternion.identity;
        e.transform.localScale = new Vector3(edge, edge, len + 0.02f);

        Renderer r = e.GetComponent<Renderer>();
        if (r != null)
            r.material = outlineMat;
    }


    private void HideLegacyWaleObjectsExceptSpecReview()
    {
        Transform[] all = GameObject.FindObjectsOfType<Transform>(true);

        int hidden = 0;

        foreach (Transform t in all)
        {
            if (t == null)
                continue;

            string n = t.name.ToUpper();

            // 새 도면기준 띠장은 유지
            if (n.Contains("WALE_SPEC_REVIEW") || n.Contains("WALE_SPEC_"))
                continue;

            // 기존 WALE 관련 오브젝트 전부 숨김
            bool isLegacyWale =
                n == "WALE" ||
                n.Contains("C605_WALE") ||
                n.Contains("FORCE_WALE") ||
                n.Contains("WALE_L") ||
                n.Contains("WALER") ||
                n.Contains("_WALE_");

            if (isLegacyWale)
            {
                t.gameObject.SetActive(false);
                hidden++;
            }
        }

        Debug.Log("기존 노란 WALE 계열 강제 숨김 수: " + hidden);
    }


    private string LoadReviewJsonText(string fileName)
    {
        string safeFileName = System.IO.Path.GetFileName(fileName);
        string nameNoExt = System.IO.Path.GetFileNameWithoutExtension(safeFileName);
        string resourcePath = "WangsukDXF/Review/" + nameNoExt;

        TextAsset ta = Resources.Load<TextAsset>(resourcePath);
        if (ta != null && !string.IsNullOrEmpty(ta.text))
        {
            Debug.Log("[REVIEW_JSON_V2] Resources 로드 성공: " + resourcePath);
            return ta.text;
        }

        if (Application.platform == RuntimePlatform.WebGLPlayer)
        {
            Debug.LogWarning("[REVIEW_JSON_V2] WebGL Resources JSON 없음: " + resourcePath);
            return null;
        }

        string path = System.IO.Path.Combine(
            Application.streamingAssetsPath,
            "WangsukDXF",
            "Review",
            safeFileName
        );

        if (!System.IO.File.Exists(path))
        {
            Debug.LogWarning("[REVIEW_JSON_V2] Editor/PC Review JSON 없음: " + path);
            return null;
        }

        string json = System.IO.File.ReadAllText(path);
        if (string.IsNullOrEmpty(json))
        {
            Debug.LogWarning("[REVIEW_JSON_V2] Editor/PC Review JSON 비어 있음: " + path);
            return null;
        }

        Debug.Log("[REVIEW_JSON_V2] Editor/PC 파일 로드 성공: " + path);
        return json;
    }



    

    private Shader GetWebSafeShader()
    {
        Shader shader = Shader.Find("Universal Render Pipeline/Lit");

        if (shader == null)
            shader = Shader.Find("Universal Render Pipeline/Unlit");

        if (shader == null)
            shader = Shader.Find("Unlit/Color");

        if (shader == null)
            shader = Shader.Find("Sprites/Default");

        if (shader == null)
        {
            Debug.LogError("[WEBGL_SHADER] 사용 가능한 기본 Shader를 찾지 못했습니다.");
            shader = Shader.Find("Hidden/InternalErrorShader");
        }

        return shader;
    }

    private Shader GetWebSafeTransparentShader()
    {
        Shader shader = Shader.Find("Universal Render Pipeline/Unlit");

        if (shader == null)
            shader = Shader.Find("Unlit/Transparent");

        if (shader == null)
            shader = Shader.Find("Sprites/Default");

        if (shader == null)
            shader = GetWebSafeShader();

        return shader;
    }


}













































