using System.IO;
using UnityEngine;

public static class DxfJsonLoader
{
    public static WangsukDxfGroupData LoadGroup(string fileName)
    {
        string safeFileName = Path.GetFileName(fileName);
        string nameNoExt = Path.GetFileNameWithoutExtension(safeFileName);

        string resourcePath = "WangsukDXF/ParsedUnityJson_C605/" + nameNoExt;

        Debug.Log("[DXF_LOADER_V2] LoadGroup 호출: " + safeFileName + " / resourcePath=" + resourcePath);

        TextAsset resourceJson = Resources.Load<TextAsset>(resourcePath);

        if (resourceJson != null && !string.IsNullOrEmpty(resourceJson.text))
        {
            WangsukDxfGroupData data = JsonUtility.FromJson<WangsukDxfGroupData>(resourceJson.text);

            if (data != null && data.entities != null)
            {
                Debug.Log("[DXF_LOADER_V2] Resources 로드 성공: " + resourcePath + " / entityCount=" + data.entities.Count);
                return data;
            }

            Debug.LogError("[DXF_LOADER_V2] Resources JSON 파싱 실패: " + resourcePath);
            return null;
        }

        if (Application.platform == RuntimePlatform.WebGLPlayer)
        {
            Debug.LogError("[DXF_LOADER_V2] WebGL Resources JSON 없음: " + resourcePath);
            return null;
        }

        string path = Path.Combine(
            Application.streamingAssetsPath,
            "WangsukDXF",
            "ParsedUnityJson_C605",
            safeFileName
        );

        if (!File.Exists(path))
        {
            Debug.LogError("[DXF_LOADER_V2] Editor/PC C605 JSON 파일 없음: " + path);
            return null;
        }

        string json = File.ReadAllText(path);

        if (string.IsNullOrEmpty(json))
        {
            Debug.LogError("[DXF_LOADER_V2] Editor/PC C605 JSON 파일 비어 있음: " + path);
            return null;
        }

        WangsukDxfGroupData fileData = JsonUtility.FromJson<WangsukDxfGroupData>(json);

        if (fileData != null && fileData.entities != null)
            Debug.Log("[DXF_LOADER_V2] Editor/PC 파일 로드 성공: " + path + " / entityCount=" + fileData.entities.Count);

        return fileData;
    }
}
