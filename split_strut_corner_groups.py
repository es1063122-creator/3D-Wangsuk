from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) BuildAll 호출부 groupKey를 STRUT_L1로 변경
text = text.replace(
'''        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT");''',
'''        BuildStrutPlanFromDxf("c605_strut_plan.json", "STRUT_L1");'''
)

# 2) group이 없으면 STRUT 이름으로 생성하던 부분 수정
text = text.replace(
'''            group = new GameObject("STRUT");''',
'''            group = new GameObject(groupKey);'''
)

# 3) BuildStrutPlanFromDxf 내부에서 코너버팀 별도 그룹 생성 코드 삽입
old = '''        GameObject group = registry.GetGroup(groupKey);

        if (group == null)
        {
            GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
            if (root == null)
                root = new GameObject("Wangsuk_CAD_3D_ROOT");

            group = new GameObject(groupKey);
            group.transform.SetParent(root.transform, false);

            Debug.LogWarning("STRUT 그룹이 없어 강제 생성했습니다.");
        }

        int strutCreated = 0;
        int beamBracingCreated = 0;'''

new = '''        GameObject group = registry.GetGroup(groupKey);

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
        int beamBracingCreated = 0;'''

if old in text:
    text = text.replace(old, new)
    print("STRUT_L1 / CORNER_STRUT_L1 그룹 분리 코드 적용")
else:
    print("그룹 생성 코드 위치를 찾지 못했습니다. 이미 수정됐거나 구조가 다릅니다.")

# 4) BEAM-BRACING 생성 대상 group을 cornerGroup으로 변경
text = text.replace(
'''                beamBracingCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "CORNER_STRUT_BODY_L1", true);''',
'''                beamBracingCreated += CreateStrutPlanPolyline(cornerGroup, e, -waleDepth1, "CORNER_STRUT_BODY_L1", true);'''
)

# 5) 일반 STRUT 이름 명확화
text = text.replace(
'''                strutCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "STRUT_L1", false);''',
'''                strutCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "STRUT_BODY_L1", false);'''
)

# 6) 로그 정리
text = text.replace(
'''Debug.Log("========== C605 STRUT 평면 검토 ==========");''',
'''Debug.Log("========== C605 STRUT / CORNER STRUT 생성 ==========");'''
)

text = text.replace(
'''Debug.Log("STRUT 일반 버팀 생성: " + strutCreated);''',
'''Debug.Log("STRUT_L1 일반 버팀 본체 생성: " + strutCreated);'''
)

text = text.replace(
'''Debug.Log("CORNER STRUT 본체 생성: " + beamBracingCreated);''',
'''Debug.Log("CORNER_STRUT_L1 본체 생성: " + beamBracingCreated);'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
