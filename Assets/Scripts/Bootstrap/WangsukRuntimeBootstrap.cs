using UnityEngine;

public class WangsukRuntimeBootstrap : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Boot()
    {
        if (GameObject.Find("WANGSUK_RUNTIME_BOOTSTRAP") != null)
            return;

        GameObject boot = new GameObject("WANGSUK_RUNTIME_BOOTSTRAP");
        DontDestroyOnLoad(boot);
        boot.AddComponent<WangsukRuntimeBootstrap>();

        Debug.Log("[WANGSUK_BOOT] Runtime bootstrap created");
    }

    private void Start()
    {
        EnsureBuilder();
        EnsureViewerUI();
        EnsureLight();
    }

    private void EnsureBuilder()
    {
        WangsukFullModelBuilder builder = FindFirstObjectByType<WangsukFullModelBuilder>();

        if (builder != null)
        {
            Debug.Log("[WANGSUK_BOOT] Existing WangsukFullModelBuilder found: " + builder.gameObject.name);
            return;
        }

        GameObject go = new GameObject("WangsukFullModelBuilder_Runtime");
        builder = go.AddComponent<WangsukFullModelBuilder>();

        Debug.Log("[WANGSUK_BOOT] WangsukFullModelBuilder added");
    }

    private void EnsureViewerUI()
    {
        WangsukViewerUI ui = FindFirstObjectByType<WangsukViewerUI>();

        if (ui != null)
        {
            Debug.Log("[WANGSUK_BOOT] Existing WangsukViewerUI found: " + ui.gameObject.name);
            return;
        }

        GameObject go = new GameObject("WangsukViewerUI_Runtime");
        ui = go.AddComponent<WangsukViewerUI>();

        Debug.Log("[WANGSUK_BOOT] WangsukViewerUI added");
    }

    private void EnsureLight()
    {
        Light[] lights = FindObjectsByType<Light>(FindObjectsSortMode.None);
        if (lights != null && lights.Length > 0)
            return;

        GameObject lightObj = new GameObject("Directional Light Runtime");
        Light light = lightObj.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.1f;
        lightObj.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        Debug.Log("[WANGSUK_BOOT] Directional light added");
    }
}
