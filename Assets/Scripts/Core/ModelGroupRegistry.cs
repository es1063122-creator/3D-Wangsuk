using System.Collections.Generic;
using UnityEngine;

public class ModelGroupRegistry : MonoBehaviour
{
    public Transform root;

    private Dictionary<string, GameObject> groups = new Dictionary<string, GameObject>();

    public void Init()
    {
        if (root == null)
        {
            GameObject rootObj = new GameObject("Wangsuk_CAD_3D_ROOT");
            root = rootObj.transform;
        }

        CreateAndRegister("PF_HPILE", "G_01_PF_HPILE");
        CreateAndRegister("CIP", "G_02_CIP");
        CreateAndRegister("WALE", "G_03_WALE");
        CreateAndRegister("ANCHOR", "G_04_ANCHOR");
        CreateAndRegister("CORNER_STRUT", "G_05_CORNER_STRUT");
        CreateAndRegister("EXCAVATION", "G_06_EXCAVATION");
        CreateAndRegister("GROUND_GL", "G_07_GROUND_GL");
        CreateAndRegister("SECTION_LINES", "G_08_SECTION_LINES");
        CreateAndRegister("GRID", "G_09_GRID");
        CreateAndRegister("LABELS", "G_10_LABELS");
        CreateAndRegister("BUILDING_PARKING", "G_11_BUILDING_PARKING");
    }

    private void CreateAndRegister(string key, string name)
    {
        if (groups.ContainsKey(key) && groups[key] != null)
            DestroyImmediate(groups[key]);

        GameObject obj = new GameObject(name);
        obj.transform.SetParent(root, false);
        groups[key] = obj;
    }

    public GameObject GetGroup(string key)
    {
        if (groups.ContainsKey(key)) return groups[key];
        return null;
    }

    public void ToggleGroup(string key)
    {
        GameObject obj = GetGroup(key);
        if (obj != null) obj.SetActive(!obj.activeSelf);
    }

    public void ShowAll()
    {
        foreach (var g in groups.Values)
            if (g != null) g.SetActive(true);
    }

    public void HideAll()
    {
        foreach (var g in groups.Values)
            if (g != null) g.SetActive(false);
    }
}

