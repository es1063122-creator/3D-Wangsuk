from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 모든 registry.ToggleGroup("그룹명") 호출을 ToggleGroupSmart("그룹명")으로 변경
text = re.sub(
    r'if \(registry != null\) registry\.ToggleGroup\("([^"]+)"\);',
    r'ToggleGroupSmart("\1");',
    text
)

helper = r'''
    private void ToggleGroupSmart(string groupName)
    {
        GameObject target = null;

        // 비활성 오브젝트까지 찾기 위해 Resources.FindObjectsOfTypeAll 사용
        GameObject[] allObjects = Resources.FindObjectsOfTypeAll<GameObject>();

        foreach (GameObject go in allObjects)
        {
            if (go == null)
                continue;

            if (go.name != groupName)
                continue;

            // Project Asset이 아니라 실제 Scene 오브젝트만 사용
            if (!go.scene.IsValid())
                continue;

            target = go;
            break;
        }

        if (target != null)
        {
            target.SetActive(!target.activeSelf);
            Debug.Log("ToggleGroupSmart: " + groupName + " => " + target.activeSelf);
            return;
        }

        if (registry != null)
        {
            registry.ToggleGroup(groupName);
            Debug.Log("ToggleGroupSmart registry fallback: " + groupName);
        }
        else
        {
            Debug.LogWarning("ToggleGroupSmart 실패: 그룹을 찾지 못함 - " + groupName);
        }
    }
'''

if "private void ToggleGroupSmart(string groupName)" not in text:
    idx = text.rfind("}")
    text = text[:idx] + helper + "\n}"
    print("ToggleGroupSmart 함수 추가 완료")
else:
    print("ToggleGroupSmart 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
