from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // C-612~C-619 전개도 기준 PILE NO 구간 경계/라벨 표시
        BuildPileSectionMarkers("c605_pf_hpile.json");'''

if "BuildPileSectionMarkers(" not in text:
    if 'BuildSectionBottomElLabels("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildSectionBottomElLabels("c605_pf_hpile.json");''',
'''        BuildSectionBottomElLabels("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 PILE 구간 경계/라벨 호출 추가 완료")
    else:
        print("BuildSectionBottomElLabels 호출을 찾지 못했습니다.")
else:
    print("PILE 구간 경계/라벨 호출 이미 있음")

helper = r'''
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

        CreatePileSectionRangeLabel(group, centers, allCenter, 1, 67, "C-612  P001~067");
        CreatePileSectionRangeLabel(group, centers, allCenter, 67, 131, "C-613  P067~131");
        CreatePileSectionRangeLabel(group, centers, allCenter, 131, 196, "C-614  P131~196");
        CreatePileSectionRangeLabel(group, centers, allCenter, 196, 248, "C-615  P196~248");
        CreatePileSectionRangeLabel(group, centers, allCenter, 248, 306, "C-616  P248~306");
        CreatePileSectionRangeLabel(group, centers, allCenter, 306, 365, "C-617  P306~365");
        CreatePileSectionRangeLabel(group, centers, allCenter, 365, 428, "C-618  P365~428");
        CreatePileSectionRangeLabel(group, centers, allCenter, 428, 492, "C-619  P428~492");

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

        float topY = 0.8f;
        float bottomY = -8.0f;

        Vector3 a = new Vector3(basePos.x, topY, basePos.z);
        Vector3 b = new Vector3(basePos.x, bottomY, basePos.z);

        GameObject marker = GameObject.CreatePrimitive(PrimitiveType.Cube);
        marker.name = "C605_PILE_SECTION_BOUNDARY_" + label;
        marker.transform.SetParent(group.transform, false);
        marker.transform.position = (a + b) * 0.5f;
        marker.transform.localScale = new Vector3(0.16f, Mathf.Abs(topY - bottomY), 0.16f);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 1f, 0.95f);
        marker.GetComponent<Renderer>().material = mat;

        Vector3 textPos = p + inward * 2.8f;
        textPos.y = topY + 0.55f;

        CreatePileMarkerText(group, label + "\n" + sheet, textPos, 0.45f, 3.0f, 0.9f);
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
        plate.transform.localScale = new Vector3(plateWidth, 0.025f, plateDepth);

        Material plateMat = new Material(Shader.Find("Standard"));
        plateMat.color = new Color(0f, 0f, 0f, 0.72f);
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

        Font font = Font.CreateDynamicFontFromOSFont("Arial", 96);
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
'''

if "private void BuildPileSectionMarkers" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("PILE 구간 경계/라벨 함수 추가 완료")
else:
    print("PILE 구간 경계/라벨 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
