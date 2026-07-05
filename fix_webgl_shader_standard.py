from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 기존 Standard / Unlit 직접 호출을 WebGL 안전 함수로 변경
text = text.replace('Shader.Find("Standard")', 'GetWebSafeShader()')
text = text.replace('Shader.Find("Unlit/Transparent")', 'GetWebSafeTransparentShader()')

# 안전 Shader 함수 추가
if "private Shader GetWebSafeShader()" not in text:
    insert_at = text.rfind("\n}")
    if insert_at < 0:
        raise SystemExit("클래스 마지막 중괄호를 찾지 못했습니다.")

    helper = r'''

    private Shader GetWebSafeShader()
    {
        Shader shader = Shader.Find("Universal Render Pipeline/Lit");

        if (shader == null)
            shader = Shader.Find("Universal Render Pipeline/Unlit");

        if (shader == null)
            shader = Shader.Find("Unlit/Color");

        if (shader == null)
            shader = Shader.Find("Sprites/Default");

        if (shader == null)
        {
            Debug.LogError("[WEBGL_SHADER] 사용 가능한 기본 Shader를 찾지 못했습니다.");
            shader = Shader.Find("Hidden/InternalErrorShader");
        }

        return shader;
    }

    private Shader GetWebSafeTransparentShader()
    {
        Shader shader = Shader.Find("Universal Render Pipeline/Unlit");

        if (shader == null)
            shader = Shader.Find("Unlit/Transparent");

        if (shader == null)
            shader = Shader.Find("Sprites/Default");

        if (shader == null)
            shader = GetWebSafeShader();

        return shader;
    }

'''
    text = text[:insert_at] + helper + text[insert_at:]

path.write_text(text, encoding="utf-8")
print("WebGL Shader 안전화 완료")
