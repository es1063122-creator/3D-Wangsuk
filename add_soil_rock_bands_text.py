from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // C-610~C-619 도면 문자 기준 지층 표현
        // 확인 지층: 매립층 / 퇴적층 / 풍화토 / 풍화암
        BuildSoilRockBandsAndLabels("c605_pf_hpile.json");'''

if "BuildSoilRockBandsAndLabels(" not in text:
    if 'BuildExcavationFaceBottomAndText("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");''',
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 지층 색띠/글씨 호출 추가 완료")
    else:
        print("BuildExcavationFaceBottomAndText 호출을 찾지 못했습니다.")
else:
    print("지층 색띠/글씨 호출 이미 있음")

helper = r'''
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

        Material fillMat = CreateSoilRockMaterial(new Color(0.62f, 0.44f, 0.25f, 1f));       // 매립층
        Material sedimentMat = CreateSoilRockMaterial(new Color(0.74f, 0.61f, 0.40f, 1f));   // 퇴적층
        Material wsMat = CreateSoilRockMaterial(new Color(0.83f, 0.67f, 0.32f, 1f));         // 풍화토
        Material wrMat = CreateSoilRockMaterial(new Color(0.48f, 0.48f, 0.43f, 1f));         // 풍화암

        int fillCount = CreateSoilBandAlongPf(layerGroup, centers, fillTop, fillBottom, fillMat, "SOIL_FILL");
        int sedimentCount = CreateSoilBandAlongPf(layerGroup, centers, sedimentTop, sedimentBottom, sedimentMat, "SOIL_SEDIMENT");
        int wsCount = CreateSoilBandAlongPf(layerGroup, centers, weatheredSoilTop, weatheredSoilBottom, wsMat, "SOIL_WEATHERED_SOIL");
        int wrCount = CreateSoilBandAlongPf(layerGroup, centers, weatheredRockTop, weatheredRockBottom, wrMat, "SOIL_WEATHERED_ROCK");

        Vector3 center = Vector3.zero;
        foreach (var p in centers)
            center += p;
        center /= centers.Count;

        // 바닥 위 검정 글씨. 한글 표시를 위해 Malgun Gothic 동적 폰트 사용.
        CreateKoreanFloorLabel(textGroup, "매립층", new Vector3(center.x - 7.2f, bottomY + 0.45f, center.z - 4.0f), 1.1f, 4.0f, 1.2f);
        CreateKoreanFloorLabel(textGroup, "퇴적층", new Vector3(center.x - 2.4f, bottomY + 0.45f, center.z - 4.0f), 1.1f, 4.0f, 1.2f);
        CreateKoreanFloorLabel(textGroup, "풍화토", new Vector3(center.x + 2.4f, bottomY + 0.45f, center.z - 4.0f), 1.1f, 4.0f, 1.2f);
        CreateKoreanFloorLabel(textGroup, "풍화암", new Vector3(center.x + 7.2f, bottomY + 0.45f, center.z - 4.0f), 1.1f, 4.0f, 1.2f);

        CreateKoreanFloorLabel(textGroup, "굴착저면  EL(+29.54~31.00)", new Vector3(center.x, bottomY + 0.48f, center.z - 6.3f), 1.05f, 9.8f, 1.25f);

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
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;
        return mat;
    }

    private int CreateSoilBandAlongPf(GameObject group, List<Vector3> centers, float topY, float bottomY, Material mat, string namePrefix)
    {
        int created = 0;

        for (int i = 0; i < centers.Count - 1; i++)
        {
            Vector3 aTop = new Vector3(centers[i].x, topY, centers[i].z);
            Vector3 bTop = new Vector3(centers[i + 1].x, topY, centers[i + 1].z);

            float dist = Vector3.Distance(aTop, bTop);

            // DXF 순서가 크게 튀는 구간은 제외
            if (dist < 0.05f || dist > 20f)
                continue;

            Vector3 aBottom = new Vector3(aTop.x, bottomY, aTop.z);
            Vector3 bBottom = new Vector3(bTop.x, bottomY, bTop.z);

            CreateExcavationWallQuad(group, aTop, bTop, bBottom, aBottom, mat, "C605_" + namePrefix + "_" + created);
            created++;
        }

        return created;
    }

    private void CreateKoreanFloorLabel(GameObject group, string label, Vector3 position, float size, float plateWidth, float plateDepth)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_SOIL_TEXT_PLATE_" + label;
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.03f, position.z);
        plate.transform.localScale = new Vector3(plateWidth, 0.025f, plateDepth);

        Material plateMat = new Material(Shader.Find("Standard"));
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

        Font font = Font.CreateDynamicFontFromOSFont("Malgun Gothic", 96);
        if (font == null)
            font = Font.CreateDynamicFontFromOSFont("Arial", 96);

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
'''

if "private void BuildSoilRockBandsAndLabels" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("지층 색띠/검정글씨 함수 추가 완료")
else:
    print("지층 색띠/검정글씨 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
