from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

signature = "private Material CreatePostPileNumberDigitMaterial()"

positions = []
start = 0
while True:
    idx = text.find(signature, start)
    if idx < 0:
        break
    positions.append(idx)
    start = idx + len(signature)

print("CreatePostPileNumberDigitMaterial count:", len(positions))

if len(positions) <= 1:
    print("중복 없음")
    path.write_text(text, encoding="utf-8")
    raise SystemExit

# 첫 번째는 남기고, 두 번째 이후 삭제
remove_ranges = []

for idx in positions[1:]:
    brace = text.find("{", idx)
    if brace < 0:
        continue

    depth = 0
    end = -1

    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end > idx:
        remove_ranges.append((idx, end))

# 뒤에서부터 삭제
for start, end in sorted(remove_ranges, reverse=True):
    text = text[:start] + "\n" + text[end:]

path.write_text(text, encoding="utf-8")
print("중복 CreatePostPileNumberDigitMaterial 제거 완료")
