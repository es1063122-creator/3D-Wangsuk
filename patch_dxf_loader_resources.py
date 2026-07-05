from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\DXF\DxfJsonLoader.cs")
text = path.read_text(encoding="utf-8")

sig = "public static WangsukDxfGroupData LoadGroup("
start = text.find(sig)
if start < 0:
    raise SystemExit("LoadGroup 메서드를 찾지 못했습니다.")

brace = text.find("{", start)
if brace < 0:
    raise SystemExit("LoadGroup 시작 중괄호를 찾지 못했습니다.")

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
    raise SystemExit("LoadGroup 끝 중괄호를 찾지 못했습니다.")

new_method = r'''
public static WangsukDxfGroupData LoadGroup(string fileName)
{
    string safeFileName = Path.GetFileName(fileName);
    string nameNoExt = Path.GetFileNameWithoutExtension(safeFileName);

    // WebGL 대응:
    // StreamingAssets는 WebGL에서 File.Exists/ReadAllText로 직접 읽을 수 없으므로
    // Resources에 복사된 JSON을 우선 사용한다.
    string resourcePath = "WangsukDXF/ParsedUnityJson_C605/" + nameNoExt;
    TextAsset resourceJson = Resources.Load<TextAsset>(resourcePath);

    if (resourceJson != null && !string.IsNullOrEmpty(resourceJson.text))
    {
        WangsukDxfGroupData data = JsonUtility.FromJson<WangsukDxfGroupData>(resourceJson.text);
        if (data != null)
        {
            Debug.Log("[DxfJsonLoader] Resources 로드 성공: " + resourcePath);
            return data;
        }
    }

    string path = Path.Combine(
        Application.streamingAssetsPath,
        "WangsukDXF",
        "ParsedUnityJson_C605",
        safeFileName
    );

#if UNITY_WEBGL && !UNITY_EDITOR
    Debug.LogError("C605 JSON 파일 없음(Resources): " + safeFileName + " / resourcePath=" + resourcePath);
    return null;
#else
    if (!File.Exists(path))
    {
        Debug.LogError("C605 JSON 파일 없음: " + path);
        return null;
    }

    string json = File.ReadAllText(path);
    if (string.IsNullOrEmpty(json))
    {
        Debug.LogError("C605 JSON 파일 비어 있음: " + path);
        return null;
    }

    return JsonUtility.FromJson<WangsukDxfGroupData>(json);
#endif
}
'''

text = text[:start] + new_method + text[end:]
path.write_text(text, encoding="utf-8")

print("DxfJsonLoader LoadGroup WebGL Resources 대응 완료")
