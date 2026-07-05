from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

signature = "private void CreatePublicTitleUI()"
start = text.find(signature)
if start < 0:
    raise SystemExit("CreatePublicTitleUI 메서드를 찾지 못했습니다.")

brace = text.find("{", start)
if brace < 0:
    raise SystemExit("CreatePublicTitleUI 시작 중괄호를 찾지 못했습니다.")

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

if end < 0:
    raise SystemExit("CreatePublicTitleUI 끝 중괄호를 찾지 못했습니다.")

new_method = r'''
private void CreatePublicTitleUI()
{
    if (canvas == null)
        return;

    GameObject old = GameObject.Find("PUBLIC_TITLE_PANEL");
    if (old != null)
        DestroyImmediate(old);

    GameObject panel = new GameObject("PUBLIC_TITLE_PANEL");
    panel.transform.SetParent(canvas.transform, false);

    RectTransform rt = panel.AddComponent<RectTransform>();

    // 우측 상단 범례와 겹치지 않도록 좌측 버튼 아래에 배치
    rt.anchorMin = new Vector2(0, 1);
    rt.anchorMax = new Vector2(0, 1);
    rt.pivot = new Vector2(0, 1);
    rt.anchoredPosition = new Vector2(20, -178);
    rt.sizeDelta = new Vector2(760, 58);

    Image bg = panel.AddComponent<Image>();
    bg.color = new Color(0.02f, 0.025f, 0.035f, 0.68f);

    GameObject titleObj = new GameObject("TitleText");
    titleObj.transform.SetParent(panel.transform, false);

    RectTransform titleRt = titleObj.AddComponent<RectTransform>();
    titleRt.anchorMin = new Vector2(0, 0.48f);
    titleRt.anchorMax = new Vector2(1, 1);
    titleRt.offsetMin = new Vector2(14, 0);
    titleRt.offsetMax = new Vector2(-14, -3);

    Text title = titleObj.AddComponent<Text>();
    title.text = "동진토건(주) 왕숙 A-6BL 흙막이 가시설 3D 검토 뷰어";
    title.alignment = TextAnchor.MiddleLeft;
    title.fontSize = 19;
    title.fontStyle = FontStyle.Bold;
    title.color = new Color(1f, 1f, 1f, 1f);
    title.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

    GameObject guideObj = new GameObject("GuideText");
    guideObj.transform.SetParent(panel.transform, false);

    RectTransform guideRt = guideObj.AddComponent<RectTransform>();
    guideRt.anchorMin = new Vector2(0, 0);
    guideRt.anchorMax = new Vector2(1, 0.48f);
    guideRt.offsetMin = new Vector2(14, 4);
    guideRt.offsetMax = new Vector2(-14, 0);

    Text guide = guideObj.AddComponent<Text>();
    guide.text = "마우스 드래그: 회전 / 휠: 확대·축소 / 우클릭 드래그: 이동";
    guide.alignment = TextAnchor.MiddleLeft;
    guide.fontSize = 13;
    guide.fontStyle = FontStyle.Normal;
    guide.color = new Color(0.78f, 0.88f, 1f, 1f);
    guide.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

    Debug.Log("[PUBLIC_TITLE] 공개용 제목 패널 생성 완료 - 좌측 배치");
}
'''

text = text[:start] + new_method + text[end:]
path.write_text(text, encoding="utf-8")

print("제목 패널 좌측 버튼 아래로 이동 완료")
