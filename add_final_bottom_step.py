from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

call = '''        // 동자리/건물선 기준 최종 바닥 단차 후보 표시
        BuildFinalBottomStepFromDongjari("c605_floor_dongjari_overlay.json");'''

if "BuildFinalBottomStepFromDongjari(" not in text:
    if 'BuildDongjariVectorOverlay("c605_floor_dongjari_overlay.json");' in text:
        text = text.replace(
'''        BuildDongjariVectorOverlay("c605_floor_dongjari_overlay.json");''',
'''        BuildDongjariVectorOverlay("c605_floor_dongjari_overlay.json");

''' + call
        )
        print("BuildAll에 최종바닥 단차 호출 추가 완료")
    elif 'BuildExcavationFaceBottomAndText("c605_pf_hpile.json");' in text:
        text = text.replace(
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");''',
'''        BuildExcavationFaceBottomAndText("c605_pf_hpile.json");

''' + call
        )
        print("BuildAll에 최종바닥 단차 호출 추가 완료")
    else:
        print("삽입 기준 호출을 찾지 못했습니다.")
else:
    print("최종바닥 단차 호출 이미 있음")

helper = r'''
    private void BuildFinalBottomStepFromDongjari(string jsonFileName)
    {
        WangsukDxfGroupData data = DxfJsonLoader.LoadGroup(jsonFileName);
        if (data == null || data.entities == null)
        {
            Debug.LogWarning("최종바닥 단차용 동자리 JSON 없음: " + jsonFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = registry.GetGroup("FINAL_BOTTOM_STEP");
        if (group == null)
        {
            group = new GameObject("FINAL_BOTTOM_STEP");
            group.transform.SetParent(root.transform, false);
            Debug.LogWarning("FINAL_BOTTOM_STEP 그룹이 없어 강제 생성했습니다.");
        }

        Material topLineMat = new Material(Shader.Find("Sprites/Default"));
        topLineMat.color = new Color(0.25f, 0.95f, 1f, 0.95f);

        Material lowerLineMat = new Material(Shader.Find("Sprites/Default"));
        lowerLineMat.color = new Color(0.05f, 0.35f, 1f, 0.85f);

        Material wallMat = new Material(Shader.Find("Standard"));
        wallMat.color = new Color(0.1f, 0.45f, 0.9f, 0.28f);
        wallMat.SetFloat("_Mode", 3f);
        wallMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        wallMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        wallMat.SetInt("_ZWrite", 0);
        wallMat.DisableKeyword("_ALPHATEST_ON");
        wallMat.EnableKeyword("_ALPHABLEND_ON");
        wallMat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        wallMat.renderQueue = 3100;

        // 현재 모델 기준:
        // 기존 바닥 위쪽 표시선, 추가 굴착 후보 하부선
        // 실제 깊이는 기초평면/단면도 확인 후 수정.
        float topY = -6.12f;
        float lowerY = -7.05f;

        int created = 0;
        int wallCreated = 0;

        foreach (var e in data.entities)
        {
            List<Vector3> rawPts = ConvertEntityPoints(e, 0f);

            if (rawPts == null || rawPts.Count < 2)
                continue;

            for (int i = 0; i < rawPts.Count - 1; i++)
            {
                Vector3 p0 = rawPts[i];
                Vector3 p1 = rawPts[i + 1];

                float len = Vector3.Distance(p0, p1);

                // 너무 짧은 해치/심볼성 조각과 너무 긴 기준선 제외
                if (len < 0.35f || len > 28f)
                    continue;

                Vector3 aTop = new Vector3(p0.x, topY, p0.z);
                Vector3 bTop = new Vector3(p1.x, topY, p1.z);
                Vector3 aLow = new Vector3(p0.x, lowerY, p0.z);
                Vector3 bLow = new Vector3(p1.x, lowerY, p1.z);

                CreateFinalBottomStepLine(group, aTop, bTop, topLineMat, "FINAL_STEP_TOP_" + created, 0.045f);
                CreateFinalBottomStepLine(group, aLow, bLow, lowerLineMat, "FINAL_STEP_LOW_" + created, 0.035f);

                // 모든 선에 벽면을 만들면 과해지므로 일정 간격으로만 수직 단차면 생성
                if (created % 3 == 0)
                {
                    CreateFinalBottomStepWall(group, aTop, bTop, bLow, aLow, wallMat, "FINAL_STEP_WALL_" + wallCreated);
                    wallCreated++;
                }

                created++;
            }
        }

        // 기본 OFF. 검토할 때 최종바닥 버튼으로 표시.
        group.SetActive(false);

        Debug.Log("========== C605 최종바닥 단차 후보 생성 ==========");
        Debug.Log("FINAL_BOTTOM_STEP 라인 생성: " + created);
        Debug.Log("FINAL_BOTTOM_STEP 단차면 생성: " + wallCreated);
        Debug.Log("동자리/건물선 기준 검토용. 실제 깊이는 기초도면 EL 확인 후 보정 필요.");
        Debug.Log("기본 OFF: 최종바닥 버튼으로 표시");
        Debug.Log("===============================================");
    }

    private void CreateFinalBottomStepLine(GameObject group, Vector3 a, Vector3 b, Material mat, string name, float width)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        LineRenderer lr = obj.AddComponent<LineRenderer>();
        lr.useWorldSpace = false;
        lr.positionCount = 2;
        lr.SetPosition(0, a);
        lr.SetPosition(1, b);
        lr.startWidth = width;
        lr.endWidth = width;
        lr.material = mat;
        lr.numCapVertices = 0;
        lr.numCornerVertices = 0;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        lr.receiveShadows = false;
    }

    private void CreateFinalBottomStepWall(GameObject group, Vector3 aTop, Vector3 bTop, Vector3 bLow, Vector3 aLow, Material mat, string name)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(group.transform, false);

        Mesh mesh = new Mesh();
        mesh.vertices = new Vector3[] { aTop, bTop, bLow, aLow };
        mesh.triangles = new int[] { 0, 1, 2, 0, 2, 3 };
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        MeshFilter mf = obj.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = obj.AddComponent<MeshRenderer>();
        mr.material = mat;
    }
'''

if "private void BuildFinalBottomStepFromDongjari" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("최종바닥 단차 함수 추가 완료")
else:
    print("최종바닥 단차 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
