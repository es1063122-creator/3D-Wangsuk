from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 1) Start/초기 UI 생성 끝부분에 자동 실행 Invoke 추가
target = '''        CreateSoilLegendUI();
    }'''

replace = '''        CreateSoilLegendUI();

        // WebGL 공개용 자동 시작
        // 링크 접속 후 0.5초 뒤 모델 생성 + 기본보기 + 3D Fit 자동 실행
        Invoke(nameof(AutoBuildForPublicView), 0.5f);
    }'''

if "Invoke(nameof(AutoBuildForPublicView)" not in text:
    if target not in text:
        raise SystemExit("CreateSoilLegendUI(); 끝 블록을 찾지 못했습니다.")
    text = text.replace(target, replace, 1)

# 2) AutoBuildForPublicView 메서드 추가
if "private void AutoBuildForPublicView()" not in text:
    marker = "    private Color GetButtonColor"
    idx = text.find(marker)

    if idx < 0:
        marker = "    private void CreateButton"
        idx = text.find(marker)

    if idx < 0:
        raise SystemExit("메서드 삽입 위치를 찾지 못했습니다.")

    method = r'''
    private void AutoBuildForPublicView()
    {
        if (builder == null)
            builder = FindObjectOfType<WangsukFullModelBuilder>();

        if (fitView == null)
            fitView = FindObjectOfType<WangsukFitView>();

        if (builder == null)
        {
            Debug.LogWarning("[PUBLIC_START] WangsukFullModelBuilder를 찾지 못했습니다.");
            return;
        }

        Debug.Log("[PUBLIC_START] WebGL 공개용 자동 모델 생성 시작");

        builder.BuildAll();

        ApplyViewPreset("basic");

        if (fitView != null)
            fitView.Fit3D();

        Debug.Log("[PUBLIC_START] 자동 생성 + 기본보기 + 3D뷰 적용 완료");
    }


'''
    text = text[:idx] + method + text[idx:]

path.write_text(text, encoding="utf-8")
print("WebGL 공개용 자동 시작 적용 완료")
