using UnityEngine;

public static class WangsukSceneNormalizer
{
    public static void NormalizeRootToOrigin(GameObject root, float extraScale = 1f)
    {
        if (root == null) return;

        bool hasBounds = false;
        Bounds bounds = new Bounds(Vector3.zero, Vector3.zero);

        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
        foreach (Renderer r in renderers)
        {
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
            if (lr.positionCount <= 0) continue;

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

        if (!hasBounds) return;

        Vector3 center = bounds.center;

        // 중심을 원점으로 이동
        root.transform.position -= center;

        // 보기용 스케일
        root.transform.localScale = Vector3.one * extraScale;

        Debug.Log("Scene Normalize 완료 / Center=" + center + " / Scale=" + extraScale);
    }
}

