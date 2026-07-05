using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class WebGLPublicPolish : MonoBehaviour
{
    private Camera cam;

    private Vector3 targetCenter;
    private Vector3 currentCenter;
    private Vector3 centerVelocity;

    private float targetYaw = 35f;
    private float targetPitch = 35f;
    private float currentYaw = 35f;
    private float currentPitch = 35f;

    private float targetDistance = 220f;
    private float currentDistance = 220f;
    private float distanceVelocity;

    private Vector3 lastMouse;

    private bool initialized;
    private bool hadTwoTouches;
    private float lastTouchDistance;
    private Vector2 lastTouchCenter;

    private const float pcRotateSensitivity = 0.22f;
    private const float pcPanSensitivity = 0.0022f;
    private const float pcZoomStep = 0.88f;

    private const float mobileRotateSensitivity = 0.13f;
    private const float mobilePanSensitivity = 0.0028f;
    private const float mobilePinchZoomSensitivity = 0.995f;

    private const float rotateSmooth = 12f;
    private const float panSmooth = 0.07f;
    private const float zoomSmooth = 0.07f;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Install()
    {
        if (GameObject.Find("WEBGL_PUBLIC_POLISH") != null)
            return;

        GameObject go = new GameObject("WEBGL_PUBLIC_POLISH");
        DontDestroyOnLoad(go);
        go.AddComponent<WebGLPublicPolish>();
    }

    private void Start()
    {
        QualitySettings.antiAliasing = 4;
        Application.targetFrameRate = 60;

        ApplyUIScalingAndFont();
        InvokeRepeating(nameof(ApplyUIScalingAndFont), 1.0f, 2.5f);

        Invoke(nameof(InitCamera), 0.8f);
        Invoke(nameof(RefreshModelBounds), 2.0f);
    }

    private void InitCamera()
    {
        DisableOtherCameraControllers();
        cam = Camera.main;
        if (cam == null)
            cam = FindFirstObjectByType<Camera>();

        if (cam == null)
        {
            Debug.LogWarning("[WEBGL_ORBIT] Camera 없음");
            return;
        }

        RefreshModelBounds();

        initialized = true;
        Debug.Log("[WEBGL_ORBIT] PC/모바일 직접 Orbit 카메라 조작 적용 완료");
    }

    private void DisableOtherCameraControllers()
    {
        OrbitCameraController[] oldOrbitControllers = FindObjectsByType<OrbitCameraController>(FindObjectsInactive.Include, FindObjectsSortMode.None);

        foreach (OrbitCameraController old in oldOrbitControllers)
        {
            if (old != null)
            {
                old.enabled = false;
                Debug.Log("[WEBGL_ORBIT] 기존 OrbitCameraController 비활성화: " + old.gameObject.name);
            }
        }
    }

    private void RefreshModelBounds()
    {
        Bounds b;
        if (TryGetModelBounds(out b))
        {
            targetCenter = b.center;
            currentCenter = targetCenter;

            float size = Mathf.Max(b.size.x, b.size.y, b.size.z);
            if (size < 10f)
                size = 120f;

            targetDistance = size * 1.45f;
            currentDistance = targetDistance;

            targetYaw = currentYaw = 35f;
            targetPitch = currentPitch = 38f;

            ApplyCameraImmediate();
            Debug.Log("[WEBGL_ORBIT] Bounds 적용 center=" + b.center + " / size=" + b.size + " / dist=" + targetDistance);
        }
        else
        {
            targetCenter = Vector3.zero;
            currentCenter = Vector3.zero;
            targetDistance = currentDistance = 220f;
            ApplyCameraImmediate();
            Debug.LogWarning("[WEBGL_ORBIT] 모델 Bounds 없음. 기본 카메라 적용");
        }
    }

    private bool TryGetModelBounds(out Bounds bounds)
    {
        bounds = new Bounds(Vector3.zero, Vector3.zero);

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        Renderer[] renderers;

        if (root != null)
            renderers = root.GetComponentsInChildren<Renderer>(true);
        else
            renderers = FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);

        bool has = false;

        foreach (Renderer r in renderers)
        {
            if (r == null)
                continue;

            if (r.GetComponentInParent<Canvas>() != null)
                continue;

            if (!has)
            {
                bounds = r.bounds;
                has = true;
            }
            else
            {
                bounds.Encapsulate(r.bounds);
            }
        }

        return has;
    }

    private void Update()
    {
        if (!initialized || cam == null)
            return;

        if (IsMobileLikeDevice() && Input.touchCount > 0)
            HandleMobileTouch();
        else
            HandlePCMouse();
    }

    private void LateUpdate()
    {
        if (!initialized || cam == null)
            return;

        ApplySmoothCamera();
    }

    private bool IsMobileLikeDevice()
    {
        if (Application.isMobilePlatform)
            return true;

        if (Input.touchSupported && Screen.width <= 1200)
            return true;

        return false;
    }

    private void HandlePCMouse()
    {
        hadTwoTouches = false;

        Vector3 mouse = Input.mousePosition;

        if (Input.GetMouseButtonDown(0) || Input.GetMouseButtonDown(1) || Input.GetMouseButtonDown(2))
            lastMouse = mouse;

        Vector3 delta = mouse - lastMouse;
        lastMouse = mouse;

        if (IsPointerOverRealUI())
            return;

        // 왼쪽 드래그: 회전
        if (Input.GetMouseButton(0))
        {
            targetYaw += delta.x * pcRotateSensitivity;
            targetPitch -= delta.y * pcRotateSensitivity;
            targetPitch = Mathf.Clamp(targetPitch, -85f, 85f);
        }

        // 오른쪽/휠버튼 드래그: 이동
        if (Input.GetMouseButton(1) || Input.GetMouseButton(2))
        {
            PanByScreenDelta(delta, pcPanSensitivity);
        }

        // 휠: 확대/축소
        float scroll = Input.mouseScrollDelta.y;
        if (Mathf.Abs(scroll) > 0.001f)
        {
            float zoomFactor = Mathf.Pow(pcZoomStep, scroll);
            targetDistance *= zoomFactor;
            targetDistance = Mathf.Clamp(targetDistance, 5f, 3000f);
        }
    }

    private void HandleMobileTouch()
    {
        if (Input.touchCount == 1)
        {
            hadTwoTouches = false;

            Touch t = Input.GetTouch(0);

            if (IsTouchOverRealUI(t.fingerId))
                return;

            if (t.phase == TouchPhase.Moved)
            {
                Vector2 d = t.deltaPosition;
                targetYaw += d.x * mobileRotateSensitivity;
                targetPitch -= d.y * mobileRotateSensitivity;
                targetPitch = Mathf.Clamp(targetPitch, -85f, 85f);
            }
        }
        else if (Input.touchCount >= 2)
        {
            Touch t0 = Input.GetTouch(0);
            Touch t1 = Input.GetTouch(1);

            if (IsTouchOverRealUI(t0.fingerId) || IsTouchOverRealUI(t1.fingerId))
                return;

            Vector2 p0 = t0.position;
            Vector2 p1 = t1.position;

            float dist = Vector2.Distance(p0, p1);
            Vector2 center = (p0 + p1) * 0.5f;

            if (!hadTwoTouches || t0.phase == TouchPhase.Began || t1.phase == TouchPhase.Began)
            {
                lastTouchDistance = dist;
                lastTouchCenter = center;
                hadTwoTouches = true;
                return;
            }

            float distDelta = dist - lastTouchDistance;
            Vector2 centerDelta = center - lastTouchCenter;

            // 두 손가락 벌리기/오므리기: 확대축소
            if (Mathf.Abs(distDelta) > 0.5f)
            {
                float zoomFactor = Mathf.Pow(mobilePinchZoomSensitivity, distDelta);
                targetDistance *= zoomFactor;
                targetDistance = Mathf.Clamp(targetDistance, 5f, 3000f);
            }

            // 두 손가락 같이 이동: 화면 이동
            if (centerDelta.sqrMagnitude > 0.1f)
            {
                PanByScreenDelta(centerDelta, mobilePanSensitivity);
            }

            lastTouchDistance = dist;
            lastTouchCenter = center;
        }
    }

    private void PanByScreenDelta(Vector2 delta, float sensitivity)
    {
        if (cam == null)
            return;

        float factor = Mathf.Max(1f, targetDistance) * sensitivity;

        Vector3 right = cam.transform.right;
        Vector3 up = cam.transform.up;

        targetCenter += (-right * delta.x - up * delta.y) * factor;
    }

    private void ApplyCameraImmediate()
    {
        currentYaw = targetYaw;
        currentPitch = targetPitch;
        currentDistance = targetDistance;
        currentCenter = targetCenter;

        ApplyCameraTransform();
    }

    private void ApplySmoothCamera()
    {
        currentYaw = Mathf.LerpAngle(currentYaw, targetYaw, Time.deltaTime * rotateSmooth);
        currentPitch = Mathf.LerpAngle(currentPitch, targetPitch, Time.deltaTime * rotateSmooth);
        currentDistance = Mathf.SmoothDamp(currentDistance, targetDistance, ref distanceVelocity, zoomSmooth);
        currentCenter = Vector3.SmoothDamp(currentCenter, targetCenter, ref centerVelocity, panSmooth);

        ApplyCameraTransform();
    }

    private void ApplyCameraTransform()
    {
        Quaternion rot = Quaternion.Euler(currentPitch, currentYaw, 0f);
        Vector3 dir = rot * Vector3.back;

        cam.transform.position = currentCenter + dir * currentDistance;
        cam.transform.rotation = rot;
        cam.transform.LookAt(currentCenter);
    }

    private bool IsPointerOverRealUI()
    {
        if (EventSystem.current == null)
            return false;

        PointerEventData data = new PointerEventData(EventSystem.current);
        data.position = Input.mousePosition;

        List<RaycastResult> results = new List<RaycastResult>();
        EventSystem.current.RaycastAll(data, results);

        foreach (RaycastResult r in results)
        {
            if (IsRealUIResult(r))
                return true;
        }

        return false;
    }

    private bool IsTouchOverRealUI(int fingerId)
    {
        if (EventSystem.current == null)
            return false;

        PointerEventData data = new PointerEventData(EventSystem.current);
        data.position = Input.GetTouch(fingerId).position;

        List<RaycastResult> results = new List<RaycastResult>();
        EventSystem.current.RaycastAll(data, results);

        foreach (RaycastResult r in results)
        {
            if (IsRealUIResult(r))
                return true;
        }

        return false;
    }

    private bool IsRealUIResult(RaycastResult r)
    {
        if (r.gameObject == null)
            return false;

        Transform t = r.gameObject.transform;

        while (t != null)
        {
            if (t.GetComponent<Button>() != null)
                return true;

            if (t.GetComponent<Toggle>() != null)
                return true;

            if (t.GetComponent<InputField>() != null)
                return true;

            t = t.parent;
        }

        return false;
    }

    private void ApplyUIScalingAndFont()
    {
        Font korean = KoreanFontProvider.Get();

        Canvas[] canvases = FindObjectsByType<Canvas>(FindObjectsSortMode.None);
        foreach (Canvas c in canvases)
        {
            c.pixelPerfect = true;

            CanvasScaler scaler = c.GetComponent<CanvasScaler>();
            if (scaler == null)
                scaler = c.gameObject.AddComponent<CanvasScaler>();

            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1280, 720);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            scaler.referencePixelsPerUnit = 100f;
            scaler.dynamicPixelsPerUnit = 4f;
        }

        Text[] texts = FindObjectsByType<Text>(FindObjectsInactive.Include, FindObjectsSortMode.None);
        foreach (Text t in texts)
        {
            if (t == null)
                continue;

            t.font = korean;
            t.resizeTextForBestFit = false;
            t.supportRichText = true;

            if (korean != null && korean.material != null)
                t.material = korean.material;

            if (t.fontSize < 18)
                t.fontSize = 18;

            string n = t.name.ToLower();
            string pn = t.transform.parent != null ? t.transform.parent.name.ToLower() : "";

            if (n.Contains("title"))
                t.fontSize = Mathf.Max(t.fontSize, 30);

            if (n.Contains("button") || pn.Contains("button"))
                t.fontSize = Mathf.Max(t.fontSize, 18);

            t.fontStyle = FontStyle.Bold;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.SetAllDirty();

            EnsureTextSharpness(t);
        }

        TextMesh[] meshes = FindObjectsByType<TextMesh>(FindObjectsInactive.Include, FindObjectsSortMode.None);
        foreach (TextMesh tm in meshes)
        {
            if (tm == null)
                continue;

            tm.font = korean;

            MeshRenderer mr = tm.GetComponent<MeshRenderer>();
            if (mr != null && korean != null && korean.material != null)
                mr.sharedMaterial = korean.material;
        }
    }

    private void EnsureTextSharpness(Text t)
    {
        if (t == null)
            return;

        Shadow shadow = t.GetComponent<Shadow>();
        if (shadow == null)
            shadow = t.gameObject.AddComponent<Shadow>();

        shadow.effectColor = new Color(0f, 0f, 0f, 0.45f);
        shadow.effectDistance = new Vector2(1f, -1f);
        shadow.useGraphicAlpha = true;
    }
}

