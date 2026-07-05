from PIL import Image
import os

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

overlay_dir = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Overlay"
)

src = os.path.join(overlay_dir, "c605_plan_overlay.png")
dst = os.path.join(overlay_dir, "c605_plan_overlay_visible.png")

if not os.path.exists(src):
    raise SystemExit("원본 c605_plan_overlay.png 없음: " + src)

img = Image.open(src).convert("RGBA")
w, h = img.size

# 연한 청회색 반투명 배경
bg = Image.new("RGBA", (w, h), (185, 220, 230, 70))

# 기존 도면선 alpha를 이용해서 어두운 선으로 다시 그림
pixels = img.load()
out = bg.copy()
out_px = out.load()

for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]
        if a > 8:
            # 도면선은 진하게
            strength = min(220, max(80, a + 60))
            out_px[x, y] = (15, 15, 15, strength)

out.save(dst)

print("저장 완료:", dst)
