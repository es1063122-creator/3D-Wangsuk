using UnityEngine;

public static class KoreanFontProvider
{
    private static Font cachedFont;

    public static Font Get()
    {
        if (cachedFont != null)
            return cachedFont;

        cachedFont = Resources.Load<Font>("Fonts/KoreanUI");

        if (cachedFont == null)
        {
            Debug.LogError("[KOREAN_FONT] Resources/Fonts/KoreanUI 폰트 로드 실패");
            cachedFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            return cachedFont;
        }

        Debug.Log("[KOREAN_FONT] 한글 폰트 로드 성공: " + cachedFont.name);

        // WebGL Legacy Text / TextMesh 한글 글리프 강제 준비
        string chars =
            "동진토건주왕숙흙막이가시설검토뷰어" +
            "스마트건설안전가시설삼차원도면검토" +
            "마우스드래그회전휠확대축소우클릭이동" +
            "한손가락두손가락확대축소이동" +
            "기본보기구조물굴착지층바닥도면검토전체보기전체숨김" +
            "표시번호앙카앵커띠장버팀코너파일구간글씨최종바닥" +
            "높이자피에프씨아이피포스트파일말뚝흙채움매립층퇴적층풍화토풍화암기반암" +
            "생성평면뷰디뷰지층범례굴착저면" +
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" +
            "+-*/=.,:;()[]{}<>~ ";

        cachedFont.RequestCharactersInTexture(chars, 12, FontStyle.Normal);
        cachedFont.RequestCharactersInTexture(chars, 15, FontStyle.Normal);
        cachedFont.RequestCharactersInTexture(chars, 18, FontStyle.Normal);
        cachedFont.RequestCharactersInTexture(chars, 24, FontStyle.Normal);
        cachedFont.RequestCharactersInTexture(chars, 32, FontStyle.Normal);
        cachedFont.RequestCharactersInTexture(chars, 48, FontStyle.Normal);
        cachedFont.RequestCharactersInTexture(chars, 64, FontStyle.Normal);

        return cachedFont;
    }
}
