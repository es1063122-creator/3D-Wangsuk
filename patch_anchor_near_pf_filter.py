from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# p0Dist / p1Dist가 선택되는 부분 뒤에 PF 근접 필터 추가
old = '''            if (p1Dist < p0Dist)
            {
                anchorHead = p1;
                anchorTail = p0;
            }
        }

        Vector3 dir = anchorTail - anchorHead;'''

new = '''            if (p1Dist < p0Dist)
            {
                anchorHead = p1;
                anchorTail = p0;
            }

            float headDistSq = GetNearestDistanceXZ(anchorHead, pfCenters);

            // C-605 ANCHOR 레이어에는 실제 평면 앵커 외에 도면 외곽/상세/기호성 선도 포함됨.
            // PF/CIP 벽체에서 너무 먼 앵커는 3D 모델 Bounds를 망가뜨리므로 제외.
            if (headDistSq > 400f) // 20유닛 거리 제곱
            {
                return 0;
            }
        }

        Vector3 dir = anchorTail - anchorHead;'''

if old in text:
    text = text.replace(old, new)
    print("앵커 PF 근접 필터 추가 완료")
else:
    print("대상 코드 위치를 찾지 못했습니다. CreateAnchorPolyline 내부 확인 필요")

# 로그 문구 변경
text = text.replace(
'''Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상만 사용. 화면표시는 벽체 기준 4m로 축소.");''',
'''Debug.Log("도면 기준: C-605 Anchor_1단 / ANCHOR 레이어 중 길이 1000 이상 + PF 주변 앵커만 사용. 화면표시는 벽체 기준 4m로 축소.");'''
)

path.write_text(text, encoding="utf-8")
print("저장 완료")
