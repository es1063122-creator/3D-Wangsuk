from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# C# 파일 안에 잘못 들어간 리터럴 \n 제거
text = text.replace("\\n\\n", "\n\n")
text = text.replace("\\n", "\n")

path.write_text(text, encoding="utf-8")
print("WangsukViewerUI.cs 안의 잘못된 \\n 문자 수정 완료")
