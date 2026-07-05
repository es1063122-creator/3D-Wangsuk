from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

old = '''            if (layer.Contains("BEAM-BRACING"))
                beamBracingCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "BEAM_BRACING_PLAN", true);
            else
                strutCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "STRUT_PLAN", false);'''

new = '''            if (layer.Contains("BEAM-BRACING"))
            {
                // C-605 BEAM-BRACING 검토 결과:
                // 긴 부재 2개는 코너 스트러트 본체, 짧은 200mm급 부재 2개는 단부/보강선 후보.
                // Unity 좌표 변환 후 길이가 1.0 미만인 것은 단부선으로 보고 일단 제외.
                List<Vector3> checkPts = ConvertEntityPoints(e, -waleDepth1);

                if (checkPts == null || checkPts.Count < 2)
                    continue;

                float checkLen = Vector3.Distance(checkPts[0], checkPts[checkPts.Count - 1]);

                if (checkLen < 1.0f)
                {
                    Debug.Log("BEAM-BRACING 짧은 단부/보강선 제외: len=" + checkLen.ToString("F3"));
                    continue;
                }

                beamBracingCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "CORNER_STRUT_BODY_L1", true);
            }
            else
            {
                strutCreated += CreateStrutPlanPolyline(group, e, -waleDepth1, "STRUT_L1", false);
            }'''

if old in text:
    text = text.replace(old, new)
    print("BEAM-BRACING 긴 부재만 코너스트러트 본체로 생성하도록 수정 완료")
else:
    print("대상 코드 블록을 찾지 못했습니다. 이미 수정됐거나 코드 구조가 다릅니다.")

text = text.replace(
    '''Debug.Log("BEAM-BRACING 코너/대각 후보 생성: " + beamBracingCreated);''',
    '''Debug.Log("CORNER STRUT 본체 생성: " + beamBracingCreated);'''
)

text = text.replace(
    '''Debug.Log("도면 검토 결과: 현재 STRUT는 WALE 1단 높이군과 일치. L2/L3 STRUT는 전개도에서 확인되지 않아 생성하지 않음.");''',
    '''Debug.Log("도면 검토 결과: 일반 STRUT는 C-605 STRUT 레이어 기준, CORNER STRUT는 BEAM-BRACING 긴 부재만 본체로 생성.");'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
