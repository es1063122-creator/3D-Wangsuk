using System;
using System.Collections.Generic;

[Serializable]
public class WangsukDxfGroupData
{
    public string group;
    public int entity_count;
    public List<WangsukDxfEntity> entities;
}

[Serializable]
public class WangsukDxfPoint
{
    public double x;
    public double y;
    public double z;
}

[Serializable]
public class WangsukDxfEntity
{
    public string source_file;
    public string type;
    public string layer;
    public int color;
    public string linetype;

    public List<WangsukDxfPoint> points;

    public WangsukDxfPoint center;
    public WangsukDxfPoint position;

    public bool has_points;
    public bool has_center;
    public bool has_position;

    public double radius;
    public string text;
    public double height;
    public double rotation;

    public string block_name;
    public bool closed;
}

