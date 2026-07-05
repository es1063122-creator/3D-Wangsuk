using UnityEngine;

public class WangsukFitView : MonoBehaviour
{
    public Camera targetCamera;
    public float padding = 1.25f;

    public void Fit()
    {
        Fit3D();
    }

    public void Fit3D()
    {
        if (targetCamera == null)
            targetCamera = Camera.main;

        if (targetCamera == null)
        {
            Debug.LogWarning("Fit3D 실패: 카메라 없음");
            return;
        }

        if (!CalculateBounds(out Bounds bounds))
            return;

        Vector3 center = bounds.center;
        float size = Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z);
        float distance = Mathf.Clamp(size * 1.8f * padding, 20f, 5000f);

        targetCamera.orthographic = false;

        OrbitCameraController orbit = targetCamera.GetComponent<OrbitCameraController>();
        if (orbit == null)
            orbit = targetCamera.gameObject.AddComponent<OrbitCameraController>();

        orbit.SetPivot(center);
        orbit.SetDistance(distance);
        orbit.SetAngles(-35f, 55f);

        targetCamera.nearClipPlane = 0.1f;
        targetCamera.farClipPlane = Mathf.Max(5000f, distance * 10f);
        targetCamera.clearFlags = CameraClearFlags.SolidColor;
        targetCamera.backgroundColor = new Color(0.10f, 0.10f, 0.10f);

        Debug.Log("C605 3D뷰 완료 / Center: " + center + " / Bounds: " + bounds.size + " / Distance: " + distance);
    }

    public void FitTopView()
    {
        if (targetCamera == null)
            targetCamera = Camera.main;

        if (targetCamera == null)
        {
            Debug.LogWarning("FitTopView 실패: 카메라 없음");
            return;
        }

        if (!CalculateBounds(out Bounds bounds))
            return;

        Vector3 center = bounds.center;

        float aspect = targetCamera.aspect;
        float halfHeight = bounds.size.z * 0.5f;
        float halfWidth = bounds.size.x * 0.5f / aspect;
        float size = Mathf.Max(halfHeight, halfWidth) * 1.08f;
        size = Mathf.Clamp(size, 10f, 3000f);

        targetCamera.orthographic = true;
        targetCamera.orthographicSize = size;
        targetCamera.transform.position = new Vector3(center.x, 500f, center.z);
        targetCamera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);

        targetCamera.nearClipPlane = 0.1f;
        targetCamera.farClipPlane = 2000f;
        targetCamera.clearFlags = CameraClearFlags.SolidColor;
        targetCamera.backgroundColor = new Color(0.10f, 0.10f, 0.10f);

        OrbitCameraController orbit = targetCamera.GetComponent<OrbitCameraController>();
        if (orbit != null)
        {
            orbit.SetPivot(center);
            orbit.SetDistance(300f);
            orbit.SetAngles(0f, 89f);
        }

        Debug.Log("C605 평면뷰 완료 / Center: " + center + " / Bounds: " + bounds.size + " / OrthoSize: " + size);
    }

    private bool CalculateBounds(out Bounds bounds)
    {
        bounds = new Bounds(Vector3.zero, Vector3.zero);

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");

        if (root == null)
        {
            Debug.LogWarning("뷰맞춤 실패: Wangsuk_CAD_3D_ROOT 없음");
            return false;
        }

        bool hasBounds = false;

        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
        foreach (Renderer r in renderers)
        {
            if (!r.enabled)
                continue;

            if (!hasBounds)
            {
                bounds = r.bounds;
                hasBounds = true;
            }
            else
            {
                bounds.Encapsulate(r.bounds);
            }
        }

        LineRenderer[] lines = root.GetComponentsInChildren<LineRenderer>(true);
        foreach (LineRenderer lr in lines)
        {
            if (!lr.enabled || lr.positionCount <= 0)
                continue;

            for (int i = 0; i < lr.positionCount; i++)
            {
                Vector3 p = lr.GetPosition(i);

                if (!hasBounds)
                {
                    bounds = new Bounds(p, Vector3.zero);
                    hasBounds = true;
                }
                else
                {
                    bounds.Encapsulate(p);
                }
            }
        }

        if (!hasBounds)
        {
            Debug.LogWarning("뷰맞춤 실패: Bounds 없음");
            return false;
        }

        return true;
    }
}

