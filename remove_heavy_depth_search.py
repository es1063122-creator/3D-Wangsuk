from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r'\n\s*public void ReapplyBottomReviewDepthEffect\s*\(\)\s*\{.*?\n\s*\}',
    re.DOTALL
)

new_func = r'''

    public void ReapplyBottomReviewDepthEffect()
    {
        // 무거운 전체 Transform 검색 금지.
        // 버튼으로 실제 켜는 주요 도면 그룹만 가볍게 처리한다.
        string[] targetNames = new string[]
        {
            "PLAN_VECTOR_OVERLAY",
            "FINAL_BOTTOM_STEP",
            "PLAN_OVERLAY",
            "FLOOR_REVIEW_INFO"
        };

        int applied = 0;

        foreach (string n in targetNames)
        {
            GameObject go = GameObject.Find(n);
            if (go == null)
                continue;

            ApplyInsideBottomOutsideCapHeight(n);
            applied++;
        }

        Debug.Log("[INSIDE_OUTSIDE_HEIGHT_LIGHT] 깊이감 가벼운 재적용 완료: " + applied);
    }'''

if pattern.search(text):
    text = pattern.sub(new_func, text)
    print("무거운 전체검색 ReapplyBottomReviewDepthEffect 제거 완료")
else:
    print("ReapplyBottomReviewDepthEffect 함수를 찾지 못했습니다.")

path.write_text(text, encoding="utf-8")
