from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

old = """            Vector3 a = centers[i];
            Vector3 b = centers[i + 1];

            float dist = Vector3.Distance(a, b);

            // 너무 큰 점프는 DXF 순서가 끊긴 구간일 가능성이 있어 제외
            if (dist > 20f)
                continue;"""

new = """            Vector3 a = centers[i];
            Vector3 b = centers[i + 1];

            float dist = Vector3.Distance(a, b);

            // 너무 큰 점프는 DXF 순서가 끊긴 구간일 가능성이 있어 제외
            if (dist > 20f)
                continue;

            // 코너에서 띠장이 서로 과하게 겹쳐 삼각형처럼 보이는 현상 완화
            Vector3 trimDir = (b - a).normalized;
            float trim = Mathf.Min(0.25f, dist * 0.20f);
            a += trimDir * trim;
            b -= trimDir * trim;"""

if old in text:
    text = text.replace(old, new)
    print("BuildWaleLevelsByPfCenters 코너 trim 적용 완료")
else:
    print("대상 코드 위치를 찾지 못했습니다. 이미 수정됐거나 코드 구조가 다릅니다.")

old2 = """        Debug.Log("주의: 현재는 평면 위치 검토용. 단수/높이는 전개도 확인 후 적용.");"""
new2 = """        Debug.Log("주의: 현재 버팀은 L1(1단) 평면 검토용만 생성 중. L2/L3는 아직 미적용.");"""

if old2 in text:
    text = text.replace(old2, new2)
    print("버팀 로그 문구 수정 완료")

path.write_text(text, encoding="utf-8")
print("저장 완료")
