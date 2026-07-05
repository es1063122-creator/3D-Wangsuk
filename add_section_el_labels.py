from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // C-612~C-619 굴착계획 전개도 기준 구간별 시공하한선 EL 표시
        BuildSectionBottomElLabels("c605_pf_hpile.json");'''

if "BuildSectionBottomElLabels(" not in text:
    if 'BuildSoilRockBandsAndLabels("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildSoilRockBandsAndLabels("c605_pf_hpile.json");''',
'''        BuildSoilRockBandsAndLabels("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 구간별 EL 글씨 호출 추가 완료")
    else:
        print("BuildSoilRockBandsAndLabels 호출을 찾지 못했습니다.")
else:
    print("구간별 EL 글씨 호출 이미 있음")

helper = r'''
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

        // 전개도 확인값 기준 1차 구간 배치.
        // 정확한 PILE 범위는 다음 단계에서 전개도 PILE NO. 구간과 더 세분화 가능.
        CreateSectionElLabelAtPfRange(group, centers, 1, 97, "EL(+30.44)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 98, 190, "EL(+31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 191, 280, "EL(+31.00)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 281, 365, "EL(+29.54)", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 366, 405, "기반암층 상단", bottomY);
        CreateSectionElLabelAtPfRange(group, centers, 406, 492, "EL(+29.54)", bottomY);

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

        pos += inward * 4.5f;
        pos.y = y + 0.20f;

        CreateSmallFloorTextPlate(group, label, pos, 0.72f, 4.8f, 1.0f);
    }

    private void CreateSmallFloorTextPlate(GameObject group, string label, Vector3 position, float size, float plateWidth, float plateDepth)
    {
        GameObject plate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        plate.name = "C605_SECTION_EL_PLATE_" + label;
        plate.transform.SetParent(group.transform, false);
        plate.transform.position = new Vector3(position.x, position.y - 0.03f, position.z);
        plate.transform.localScale = new Vector3(plateWidth, 0.025f, plateDepth);

        Material plateMat = new Material(Shader.Find("Standard"));
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

if "private void BuildSectionBottomElLabels" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("구간별 EL 글씨 함수 추가 완료")
else:
    print("구간별 EL 글씨 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
