from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

old = '''        Debug.Log("========== C605 바닥 EL 구역 색상 생성 ==========");'''

new = '''        // EL구역 큰 면은 검토용이므로 기본 OFF
        group.SetActive(false);

        Debug.Log("========== C605 바닥 EL 구역 색상 생성 ==========");'''

if old in text and "EL구역 큰 면은 검토용이므로 기본 OFF" not in text:
    text = text.replace(old, new)
    print("BOTTOM_EL_ZONE 기본 OFF 처리 완료")
else:
    print("이미 처리됐거나 기준 문구 없음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
