from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
lines = path.read_text(encoding="utf-8").splitlines()

seen_ui = False
out = []

for line in lines:
    if line.strip() == "using UnityEngine.UI;":
        if seen_ui:
            continue
        seen_ui = True
    out.append(line)

path.write_text("\n".join(out) + "\n", encoding="utf-8")
print("using UnityEngine.UI 중복 정리 완료")
