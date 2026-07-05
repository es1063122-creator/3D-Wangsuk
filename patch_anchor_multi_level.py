from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

old = '''        List<Vector3> pfCentersForAnchor = LoadPfCentersForAnchorHead();

        int created = 0;
        foreach (var e in data.entities)
        {
            created += CreateAnchorPolyline(group, e, -waleDepth1, "ANCHOR_L1", pfCentersForAnchor);
        }

        Debug.Log("========== C605 ANCHOR 생성 ==========");
        Debug.Log("ANCHOR_L1 본체 생성: " + created);
        Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상 + PF 주변 앵커만 사용. 화면표시는 벽체 기준 4m로 축소.");
        Debug.Log("====================================");'''

new = '''        List<Vector3> pfCentersForAnchor = LoadPfCentersForAnchorHead();

        int createdL1 = 0;
        int createdL2 = 0;
        int createdL3 = 0;

        foreach (var e in data.entities)
        {
            int levelCount = GetAnchorLevelCountByNearestPf(e, pfCentersForAnchor);

            createdL1 += CreateAnchorPolyline(group, e, -waleDepth1, "ANCHOR_L1", pfCentersForAnchor);

            if (levelCount >= 2)
                createdL2 += CreateAnchorPolyline(group, e, -waleDepth2, "ANCHOR_L2", pfCentersForAnchor);

            if (levelCount >= 3)
                createdL3 += CreateAnchorPolyline(group, e, -waleDepth3, "ANCHOR_L3", pfCentersForAnchor);
        }

        Debug.Log("========== C605 ANCHOR 생성 ==========");
        Debug.Log("ANCHOR_L1 본체 생성: " + createdL1);
        Debug.Log("ANCHOR_L2 본체 생성: " + createdL2);
        Debug.Log("ANCHOR_L3 본체 생성: " + createdL3);
        Debug.Log("도면 기준: 전개도상 앵커/띠장 다단 배치 확인. PF 번호별 WALE 단수 기준으로 앵커 2단/3단 생성. 화면표시는 벽체 기준 4m로 축소.");
        Debug.Log("====================================");'''

if old in text:
    text = text.replace(old, new)
    print("BuildAnchorL1FromDxf 앵커 다단 생성으로 변경 완료")
else:
    print("기준 블록을 찾지 못했습니다. 현재 BuildAnchorL1FromDxf 구조 확인 필요")

helper = r'''
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
'''

if "private int GetAnchorLevelCountByNearestPf" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("GetAnchorLevelCountByNearestPf helper 추가 완료")
else:
    print("GetAnchorLevelCountByNearestPf helper 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
