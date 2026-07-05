using UnityEngine;

public class OrbitCameraController : MonoBehaviour
{
    [Header("3D BIM Orbit Camera")]
    public Transform pivot;
    public float distance = 180f;
    public float minDistance = 5f;
    public float maxDistance = 2000f;

    public float rotateSpeed = 0.25f;
    public float panSpeed = 0.08f;
    public float zoomSpeed = 20f;

    public float yaw = 0f;
    public float pitch = 55f;

    private Camera cam;
    private Vector3 lastMouse;

    void Awake()
    {
        cam = GetComponent<Camera>();
        EnsurePivot();
    }

    void Start()
    {
        ApplyCamera();
    }

    void EnsurePivot()
    {
        if (pivot != null)
            return;

        GameObject p = GameObject.Find("Wangsuk_Camera_Pivot");
        if (p == null)
            p = new GameObject("Wangsuk_Camera_Pivot");

        pivot = p.transform;
        pivot.position = Vector3.zero;
    }

    void Update()
    {
        if (cam == null)
            cam = GetComponent<Camera>();

        EnsurePivot();

        float scroll = Input.mouseScrollDelta.y;
        if (Mathf.Abs(scroll) > 0.001f)
        {
            distance -= scroll * zoomSpeed;
            distance = Mathf.Clamp(distance, minDistance, maxDistance);
            ApplyCamera();
        }

        if (Input.GetMouseButtonDown(1))
            lastMouse = Input.mousePosition;

        if (Input.GetMouseButton(1))
        {
            Vector3 delta = Input.mousePosition - lastMouse;
            lastMouse = Input.mousePosition;

            yaw += delta.x * rotateSpeed;
            pitch -= delta.y * rotateSpeed;
            pitch = Mathf.Clamp(pitch, 10f, 85f);

            ApplyCamera();
        }

        if (Input.GetMouseButtonDown(2))
            lastMouse = Input.mousePosition;

        if (Input.GetMouseButton(2))
        {
            Vector3 delta = Input.mousePosition - lastMouse;
            lastMouse = Input.mousePosition;

            Vector3 right = transform.right;
            Vector3 forward = Vector3.Cross(right, Vector3.up).normalized;

            float scale = distance * panSpeed * 0.01f;
            pivot.position -= right * delta.x * scale;
            pivot.position -= forward * delta.y * scale;

            ApplyCamera();
        }

        if (Input.GetKeyDown(KeyCode.R))
        {
            WangsukFitView fit = GetComponent<WangsukFitView>();
            if (fit != null)
                fit.Fit3D();
        }

        if (Input.GetKeyDown(KeyCode.T))
        {
            WangsukFitView fit = GetComponent<WangsukFitView>();
            if (fit != null)
                fit.FitTopView();
        }
    }

    public void SetPivot(Vector3 center)
    {
        EnsurePivot();
        pivot.position = center;
        ApplyCamera();
    }

    public void SetDistance(float value)
    {
        distance = Mathf.Clamp(value, minDistance, maxDistance);
        ApplyCamera();
    }

    public void SetAngles(float newYaw, float newPitch)
    {
        yaw = newYaw;
        pitch = Mathf.Clamp(newPitch, 10f, 85f);
        ApplyCamera();
    }

    public void ApplyCamera()
    {
        EnsurePivot();

        if (cam != null)
            cam.orthographic = false;

        Quaternion rot = Quaternion.Euler(pitch, yaw, 0f);
        Vector3 dir = rot * Vector3.forward;

        transform.position = pivot.position - dir * distance;
        transform.LookAt(pivot.position);

        if (cam != null)
        {
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = Mathf.Max(5000f, distance * 10f);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.10f, 0.10f, 0.10f);
        }
    }
}

