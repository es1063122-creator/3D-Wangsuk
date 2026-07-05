from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# 1) Review JSON 공통 로더 추가
if "LoadReviewJsonText" not in text:
    insert_at = text.rfind("\n    private Shader GetWebSafeShader()")
    if insert_at < 0:
        insert_at = text.rfind("\n}")
    if insert_at < 0:
        raise SystemExit("클래스 끝 위치를 찾지 못했습니다.")

    helper = r'''

    private string LoadReviewJsonText(string fileName)
    {
        string safeFileName = System.IO.Path.GetFileName(fileName);
        string nameNoExt = System.IO.Path.GetFileNameWithoutExtension(safeFileName);
        string resourcePath = "WangsukDXF/Review/" + nameNoExt;

        TextAsset ta = Resources.Load<TextAsset>(resourcePath);
        if (ta != null && !string.IsNullOrEmpty(ta.text))
        {
            Debug.Log("[REVIEW_JSON_V2] Resources 로드 성공: " + resourcePath);
            return ta.text;
        }

        if (Application.platform == RuntimePlatform.WebGLPlayer)
        {
            Debug.LogWarning("[REVIEW_JSON_V2] WebGL Resources JSON 없음: " + resourcePath);
            return null;
        }

        string path = System.IO.Path.Combine(
            Application.streamingAssetsPath,
            "WangsukDXF",
            "Review",
            safeFileName
        );

        if (!System.IO.File.Exists(path))
        {
            Debug.LogWarning("[REVIEW_JSON_V2] Editor/PC Review JSON 없음: " + path);
            return null;
        }

        string json = System.IO.File.ReadAllText(path);
        if (string.IsNullOrEmpty(json))
        {
            Debug.LogWarning("[REVIEW_JSON_V2] Editor/PC Review JSON 비어 있음: " + path);
            return null;
        }

        Debug.Log("[REVIEW_JSON_V2] Editor/PC 파일 로드 성공: " + path);
        return json;
    }

'''
    text = text[:insert_at] + helper + text[insert_at:]

# 2) post_pile_number_points_v1.json 직접 File.Exists/ReadAllText 블록 교체
pattern = re.compile(
r'''string\s+jsonPath\s*=\s*Path\.Combine\(Application\.streamingAssetsPath,\s*"WangsukDXF",\s*"Review",\s*"post_pile_number_points_v1\.json"\);\s*

\s*if\s*\(!File\.Exists\(jsonPath\)\)
\s*\{
\s*Debug\.LogWarning\("\[POST_PILE_NUMBER\] 번호 좌표 JSON 없음: "\s*\+\s*jsonPath\);
\s*return;
\s*\}

\s*PostPileNumberPointRoot\s+root\s*=\s*JsonUtility\.FromJson<PostPileNumberPointRoot>\(File\.ReadAllText\(jsonPath\)\);''',
re.MULTILINE
)

replacement = '''string json = LoadReviewJsonText("post_pile_number_points_v1.json");
        if (string.IsNullOrEmpty(json))
        {
            Debug.LogWarning("[POST_PILE_NUMBER] 번호 좌표 JSON 없음(Resources): post_pile_number_points_v1.json");
            return;
        }

        PostPileNumberPointRoot root = JsonUtility.FromJson<PostPileNumberPointRoot>(json);'''

text2, count = pattern.subn(replacement, text)

if count == 0:
    print("주의: post_pile_number 직접 블록 자동 교체 실패. 수동 확인 필요.")
else:
    print("post_pile_number Review JSON 로더 교체 완료:", count)

path.write_text(text2, encoding="utf-8")
