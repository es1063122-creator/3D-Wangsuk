from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // 도면 PILE NO 기준 바닥 EL 구간 경계선 표시
        BuildBottomZoneLines("c605_pf_hpile.json");'''

if "BuildBottomZoneLines(" not in text:
    if 'BuildSectionBottomElLabels("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildSectionBottomElLabels("c605_pf_hpile.json");''',
'''        BuildSectionBottomElLabels("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 바닥 구간선 호출 추가 완료")
    else:
        print("BuildSectionBottomElLabels 호출을 찾지 못했습니다.")
else:
    print("바닥 구간선 호출 이미 있음")

# 구간EL 글씨를 더 작게 정리
text = text.replace(
    'CreateSmallFloorTextPlate(group, label, pos, 0.38f, 5.2f, 0.72f);',
    'CreateSmallFloorTextPlate(group, label, pos, 0.30f, 4.2f, 0.55f);'
)

# 구간EL 위치를 벽체 가까이로
text = text.replace(
    'pos += inward * 2.2f;',
    'pos += inward * 1.8f;'
)

helper = r'''
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

        Vector3 a = new Vector3(p.x, y, p.z) + inward * 0.8f;
        Vector3 b = new Vector3(p.x, y, p.z) + inward * 7.5f;

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.1f)
            return;

        GameObject line = GameObject.CreatePrimitive(PrimitiveType.Cube);
        line.name = "C605_BOTTOM_ZONE_LINE_P" + pfNo;
        line.transform.SetParent(group.transform, false);
        line.transform.position = (a + b) * 0.5f;
        line.transform.localScale = new Vector3(0.045f, 0.035f, len);
        line.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        Material mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(1f, 1f, 1f, 0.72f);
        line.GetComponent<Renderer>().material = mat;
    }
'''

if "private void BuildBottomZoneLines" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("바닥 구간선 함수 추가 완료")
else:
    print("바닥 구간선 함수 이미 있음")

# 검토용 그룹 기본 OFF 처리 추가
# 생성 후 로그 전에 group.SetActive(false)를 넣는 방식
text = text.replace(
'''        Debug.Log("========== C605 구간별 굴착저면 EL 글씨 생성 ==========");''',
'''        // 구간 EL 라벨은 검토용이므로 기본 OFF
        group.SetActive(false);

        Debug.Log("========== C605 구간별 굴착저면 EL 글씨 생성 ==========");'''
)

text = text.replace(
'''        Debug.Log("========== C605 PILE 구간 경계/라벨 생성 ==========");''',
'''        // PILE 구간 마커는 검토용이므로 기본 OFF
        group.SetActive(false);

        Debug.Log("========== C605 PILE 구간 경계/라벨 생성 ==========");'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
