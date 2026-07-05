from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // C-605 바닥 동자리/건물선 벡터 오버레이
        BuildDongjariVectorOverlay("c605_floor_dongjari_overlay.json");'''

if "BuildDongjariVectorOverlay(" not in text:
    if 'BuildC605PlanOverlay("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildC605PlanOverlay("c605_pf_hpile.json");''',
'''        BuildC605PlanOverlay("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 동자리 벡터 오버레이 호출 추가 완료")
    elif 'BuildExcavationFaceBottomAndText("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");''',
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 동자리 벡터 오버레이 호출 추가 완료")
    else:
        print("삽입 기준 호출을 찾지 못했습니다.")
else:
    print("동자리 벡터 오버레이 호출 이미 있음")

helper = r'''
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
        mat.color = new Color(0.02f, 0.02f, 0.02f, 0.92f);

        int created = 0;
        float y = -6.58f;

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
        lr.startWidth = 0.028f;
        lr.endWidth = 0.028f;
        lr.material = mat;
        lr.numCapVertices = 0;
        lr.numCornerVertices = 0;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        lr.receiveShadows = false;
    }
'''

if "private void BuildDongjariVectorOverlay" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("동자리 벡터 오버레이 함수 추가 완료")
else:
    print("동자리 벡터 오버레이 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
