from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) waleDepth4 없으면 추가
if "waleDepth4" not in text:
    marker = "public class WangsukFullModelBuilder"
    idx = text.find("{", text.find(marker))
    if idx >= 0:
        text = text[:idx+1] + "\n    [SerializeField] private float waleDepth4 = 7.1f;\n" + text[idx+1:]
        print("waleDepth4 추가 완료")
    else:
        print("클래스 시작 위치를 찾지 못했습니다.")
else:
    print("waleDepth4 이미 있음")

# 2) BuildAll 쪽 호출 추가
call = '''        // C-616~C-618 전개도 검토 기준 4단 띠장 강제 보강
        BuildForceWaleLevel4FromPfCenters("c605_pf_hpile.json");'''

if "BuildForceWaleLevel4FromPfCenters(" not in text:
    # WALE 생성 이후가 가장 좋음
    candidates = [
        'BuildWaleFromPfCenters("c605_pf_hpile.json");',
        'BuildWaleByPfCenters("c605_pf_hpile.json");',
        'BuildC605WaleFromPfCenters("c605_pf_hpile.json");',
        'BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");'
    ]

    inserted = False
    for c in candidates:
        if c in text:
            text = text.replace(c, c + "\n\n" + call)
            print("4단 띠장 호출 추가 완료 기준:", c)
            inserted = True
            break

    if not inserted:
        print("기준 호출을 찾지 못했습니다. 수동 위치 확인 필요")
else:
    print("4단 띠장 호출 이미 있음")

helper = r'''
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

        Material mat = new Material(Shader.Find("Standard"));
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
'''

if "private void BuildForceWaleLevel4FromPfCenters" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("4단 띠장 강제 보강 함수 추가 완료")
else:
    print("4단 띠장 강제 보강 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
