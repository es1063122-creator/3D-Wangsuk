from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) waleDepth4 필드가 없으면 waleDepth3 근처에 추가
if "waleDepth4" not in text:
    m = re.search(r'(waleDepth3\s*=\s*[^;]+;)', text)
    if m:
        insert_pos = m.end()
        text = text[:insert_pos] + "\n    [SerializeField] private float waleDepth4 = 7.1f;" + text[insert_pos:]
        print("waleDepth4 추가 완료")
    else:
        # fallback: 클래스 시작부 뒤에 추가
        m2 = re.search(r'public class WangsukFullModelBuilder[^{]*\{', text)
        if m2:
            insert_pos = m2.end()
            text = text[:insert_pos] + "\n    [SerializeField] private float waleDepth4 = 7.1f;\n" + text[insert_pos:]
            print("waleDepth4 fallback 추가 완료")
        else:
            print("waleDepth4 삽입 위치를 찾지 못했습니다.")
else:
    print("waleDepth4 이미 있음")

# 2) 기존 단수 판정 함수를 4단 포함으로 교체
func_name = "GetSupportLevelCountByNearestPf"
start = text.find("    private int " + func_name)
if start >= 0:
    brace = text.find("{", start)
    depth = 0
    end = brace

    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    new_func = r'''    private int GetSupportLevelCountByNearestPf(WangsukDxfEntity e, List<Vector3> pfCenters)
    {
        if (pfCenters == null || pfCenters.Count == 0)
            return 3;

        List<Vector3> pts = ConvertEntityPoints(e, 0f);
        if (pts == null || pts.Count == 0)
            return 3;

        Vector3 center = Vector3.zero;
        foreach (var p in pts)
            center += p;
        center /= pts.Count;

        int nearestIndex = 0;
        float bestDist = float.MaxValue;

        for (int i = 0; i < pfCenters.Count; i++)
        {
            float d = Vector3.SqrMagnitude(center - pfCenters[i]);
            if (d < bestDist)
            {
                bestDist = d;
                nearestIndex = i;
            }
        }

        int pfNo = nearestIndex + 1;

        return GetWaleLevelCountByPfNo(pfNo);
    }

    private int GetWaleLevelCountByPfNo(int pfNo)
    {
        // CAD 전개도 C-612~C-619 재검토 기준.
        // C-616(P248~306), C-617(P306~365)는 4단 띠장 후보가 확인되어 4단 반영.
        // C-618(P365~428)은 복합 후보이나 우선 4단 검토 반영.
        // 추후 기초/단면도와 최종 대조 후 구간을 더 세분화.
        if (pfNo >= 248 && pfNo <= 428)
            return 4;

        // 나머지는 우선 3단 기준으로 통일.
        // 기존 2단 처리 구간도 전개도 WALE/C-WALE 표현상 3단 후보가 있어 검토 모델에서는 3단 표시.
        return 3;
    }'''

    text = text[:start] + new_func + text[end:]
    print("GetSupportLevelCountByNearestPf / GetWaleLevelCountByPfNo 4단 기준으로 교체 완료")
else:
    print("GetSupportLevelCountByNearestPf 함수를 찾지 못했습니다.")

# 3) CreateStrutPlanPolylineByWaleLevels 함수가 있으면 4단 생성 추가
func_name = "CreateStrutPlanPolylineByWaleLevels"
start = text.find("    private int " + func_name)
if start >= 0:
    brace = text.find("{", start)
    depth = 0
    end = brace

    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    new_func = r'''    private int CreateStrutPlanPolylineByWaleLevels(GameObject group, WangsukDxfEntity e, string label, bool isBeamBracing, int levelCount)
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
    }'''

    text = text[:start] + new_func + text[end:]
    print("STRUT/CORNER_STRUT 4단 연동 함수 교체 완료")
else:
    print("CreateStrutPlanPolylineByWaleLevels 함수를 찾지 못했습니다.")

# 4) WALE 생성 쪽에서 4단 helper가 없으면, waleDepth3까지만 생성하는 패턴을 보강
# 대표 패턴: levelCount >= 3 다음에 4단 추가
if "WALE_BODY_L4" not in text and "waleDepth4" in text:
    text = text.replace(
'''        if (levelCount >= 3)
            created += CreateWaleSegment(group, p0, p1, -waleDepth3, "WALE_BODY_L3");''',
'''        if (levelCount >= 3)
            created += CreateWaleSegment(group, p0, p1, -waleDepth3, "WALE_BODY_L3");

        if (levelCount >= 4)
            created += CreateWaleSegment(group, p0, p1, -waleDepth4, "WALE_BODY_L4");'''
    )

    text = text.replace(
'''        if (levelCount >= 3)
            CreateWaleSegment(group, p0, p1, -waleDepth3, "WALE_BODY_L3");''',
'''        if (levelCount >= 3)
            CreateWaleSegment(group, p0, p1, -waleDepth3, "WALE_BODY_L3");

        if (levelCount >= 4)
            CreateWaleSegment(group, p0, p1, -waleDepth4, "WALE_BODY_L4");'''
    )
    print("WALE_BODY_L4 패턴 보강 시도 완료")
else:
    print("WALE_BODY_L4 이미 있거나 별도 패턴 필요")

# 5) 로그 문구 보정
text = text.replace(
    "P001~P097=2단, P098~P365=3단, P366~P405=2단, P406~P492=3단",
    "C-612~C-619 전개도 재검토 기준: P248~P428=4단 후보 반영, 기타=3단 검토"
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
