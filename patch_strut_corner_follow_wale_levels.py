from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) strut 생성 카운터 뒤에 PF center 로드 추가
old_counter = '''        int strutCreated = 0;
        int beamBracingCreated = 0;'''

new_counter = '''        int strutCreated = 0;
        int beamBracingCreated = 0;

        // STRUT / CORNER STRUT 수직 단수는 전개도 WALE 단수 기준으로 맞춘다.
        // 평면 위치는 C-605 STRUT / BEAM-BRACING 도형 그대로 사용.
        List<Vector3> pfCentersForStrutLevels = LoadPfCentersForStrutLevelMatching();'''

if old_counter in text and "pfCentersForStrutLevels" not in text:
    text = text.replace(old_counter, new_counter)
    print("STRUT 단수 매칭용 PF center 로드 추가 완료")
else:
    print("PF center 로드 코드 이미 있음 또는 기준 문구 없음")

# 2) 일반 STRUT 1단 생성 코드를 다단 생성으로 변경
old_strut = '''                strutCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "STRUT_BODY_L1", false);'''

new_strut = '''                int levelCount = GetStrutLevelCountByNearestPf(e, pfCentersForStrutLevels);
                strutCreated += CreateStrutPlanPolylineByWaleLevels(group, e, "STRUT_BODY", false, levelCount);'''

if old_strut in text:
    text = text.replace(old_strut, new_strut)
    print("일반 STRUT 다단 생성으로 변경 완료")
else:
    print("일반 STRUT 1단 생성 기준 문구를 찾지 못했습니다. 이미 수정됐을 수 있습니다.")

# 3) CORNER STRUT 1단 생성 코드를 다단 생성으로 변경
old_corner = '''                beamBracingCreated += CreateStrutPlanPolyline(cornerGroup, e, -waleDepth1, "CORNER_STRUT_BODY_L1", true);'''

new_corner = '''                int levelCount = GetStrutLevelCountByNearestPf(e, pfCentersForStrutLevels);
                beamBracingCreated += CreateStrutPlanPolylineByWaleLevels(cornerGroup, e, "CORNER_STRUT_BODY", true, levelCount);'''

if old_corner in text:
    text = text.replace(old_corner, new_corner)
    print("CORNER STRUT 다단 생성으로 변경 완료")
else:
    print("CORNER STRUT 1단 생성 기준 문구를 찾지 못했습니다. 이미 수정됐을 수 있습니다.")

# 4) 로그 문구 수정
text = text.replace(
'''Debug.Log("도면 검토 결과: 일반 STRUT는 C-605 STRUT 레이어 기준, CORNER STRUT는 BEAM-BRACING 긴 부재만 본체로 생성.");''',
'''Debug.Log("도면 기준: STRUT/CORNER STRUT 평면 위치는 C-605 기준, 수직 단수는 WALE 단수 기준으로 2단/3단 생성.");'''
)

# 5) helper 함수 추가
helper = r'''
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
        // P001~P097=2단, P098~P365=3단, P366~P405=2단, P406~P492=3단
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

        return created;
    }
'''

if "private List<Vector3> LoadPfCentersForStrutLevelMatching()" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("STRUT WALE 단수 연동 helper 추가 완료")
else:
    print("STRUT helper 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
