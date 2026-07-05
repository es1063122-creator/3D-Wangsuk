using UnityEngine;

public static class CadCoordinateSystem
{
    public static double OriginX = -16000000.0;
    public static double OriginY = 3000000.0;

    // 기존 0.001보다 5배 축소
    // DXF 전체 단지/가시설을 Unity 화면에 보기 쉽게 조정
    public static float Scale = 0.0002f;

    public static Vector3 ToUnity(double dxfX, double dxfY, double dxfZ = 0)
    {
        float x = (float)((dxfX - OriginX) * Scale);
        float z = (float)((dxfY - OriginY) * Scale);
        float y = (float)(dxfZ * Scale);
        return new Vector3(x, y, z);
    }

    public static Vector3 ToUnityPoint(WangsukDxfPoint p)
    {
        if (p == null)
            return Vector3.zero;

        return ToUnity(p.x, p.y, p.z);
    }
}

