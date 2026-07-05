from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

old = '''        // 실제 앵커는 너무 길어서 3D 검토 화면을 망가뜨리므로 표시 길이를 제한한다.
        // CAD 원본 길이는 JSON에 보존되어 있고, Unity에서는 벽체 외측 방향 표시용으로 짧게 표현.
        float displayLen = Mathf.Min(originalLen, 4.0f);

        Vector3 a = anchorHead;
        Vector3 b = anchorHead + dir * displayLen;'''

new = '''        // C-605 평면도 Anchor_1단 긴 본체 대표 길이: 약 12280.6mm
        // Unity 변환 기준으로 약 12.28m를 실제 앵커 표시 길이로 사용한다.
        // 단, CAD 원본 길이가 더 짧으면 원본 길이를 우선한다.
        float displayLen = Mathf.Min(originalLen, 12.28f);

        // 앵커는 배면지반 방향으로 하향 설치되는 것으로 3D 표현한다.
        // 도면상 별도 설치각 숫자가 확인되기 전까지 검토용 하향각 15도 적용.
        float downwardAngleDeg = 15.0f;
        float downwardRad = downwardAngleDeg * Mathf.Deg2Rad;

        Vector3 horizontalDir = new Vector3(dir.x, 0f, dir.z);
        if (horizontalDir.sqrMagnitude < 0.0001f)
            horizontalDir = dir;

        horizontalDir.Normalize();

        Vector3 slopedDir = horizontalDir * Mathf.Cos(downwardRad) + Vector3.down * Mathf.Sin(downwardRad);

        Vector3 a = anchorHead;
        Vector3 b = anchorHead + slopedDir.normalized * displayLen;'''

if old in text:
    text = text.replace(old, new)
    print("앵커 길이 12.28m + 하향 15도 적용 완료")
else:
    print("기준 문구를 찾지 못했습니다. CreateAnchorPolyline 함수 확인 필요")

# 스케일/회전이 dir 기준이면 slopedDir 기준으로 변경
text = text.replace(
'''        anchor.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);''',
'''        anchor.transform.rotation = Quaternion.LookRotation(slopedDir.normalized, Vector3.up);'''
)

text = text.replace(
'''        anchor.transform.localScale = new Vector3(0.08f, 0.08f, displayLen);''',
'''        anchor.transform.localScale = new Vector3(0.08f, 0.08f, displayLen);'''
)

# 로그 문구 교체
text = text.replace(
'''Debug.Log("도면 기준: 전개도상 앵커/띠장 다단 배치 확인. PF 번호별 WALE 단수 기준으로 앵커 2단/3단 생성. 화면표시는 벽체 기준 4m로 축소.");''',
'''Debug.Log("도면 기준: 앵커는 PF 번호별 WALE 단수 기준 2단/3단 생성, C-605 평면각 유지, 길이 약 12.28m, 하향각 15도 적용.");'''
)

text = text.replace(
'''Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상 + PF 주변 앵커만 사용. 화면표시는 벽체 기준 4m로 축소.");''',
'''Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상 + PF 주변 앵커만 사용. 길이 약 12.28m, 하향각 15도 적용.");'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
