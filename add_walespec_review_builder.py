from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\Builders\WangsukFullModelBuilder.cs")
text = path.read_text(encoding="utf-8")

# using 보강
if "using System.Collections.Generic;" not in text:
    text = text.replace("using UnityEngine;", "using UnityEngine;\nusing System.Collections.Generic;")

# 호출 추가
call = '        BuildWaleSpecReviewFromPfCenters("c605_pf_hpile.json");'

if 'BuildWaleSpecReviewFromPfCenters("c605_pf_hpile.json")' not in text:
    inserted = False

    # 강제 4단 함수 뒤에 넣으면 기존/검토용 둘 다 비교 가능
    target = 'BuildForceWaleLevel4FromPfCenters("c605_pf_hpile.json");'
    if target in text:
        text = text.replace(target, target + "\n\n" + call)
        inserted = True
        print("도면띠장 호출 추가 위치: BuildForceWaleLevel4FromPfCenters 뒤")
    else:
        # fallback: 기존 WALE 생성 함수 뒤
        candidates = [
            'BuildWaleFromPfCenters("c605_pf_hpile.json");',
            'BuildWaleByPfCenters("c605_pf_hpile.json");',
            'BuildC605WaleFromPfCenters("c605_pf_hpile.json");'
        ]

        for c in candidates:
            if c in text:
                text = text.replace(c, c + "\n\n" + call)
                inserted = True
                print("도면띠장 호출 추가 위치:", c)
                break

    if not inserted:
        print("주의: 호출 위치를 자동으로 찾지 못했습니다. 함수는 추가되지만 호출은 수동 확인 필요.")
else:
    print("도면띠장 호출 이미 있음")

helper = r'''
    private class WaleSpecRange
    {
        public int startPf;
        public int endPf;
        public int bandIndex;
        public bool doubleH;
        public string source;

        public WaleSpecRange(int startPf, int endPf, int bandIndex, bool doubleH, string source)
        {
            this.startPf = startPf;
            this.endPf = endPf;
            this.bandIndex = bandIndex;
            this.doubleH = doubleH;
            this.source = source;
        }
    }

    private void BuildWaleSpecReviewFromPfCenters(string pfFileName)
    {
        WangsukDxfGroupData pfData = DxfJsonLoader.LoadGroup(pfFileName);
        if (pfData == null || pfData.entities == null)
        {
            Debug.LogWarning("WALE_SPEC_REVIEW PF JSON 없음: " + pfFileName);
            return;
        }

        GameObject root = GameObject.Find("Wangsuk_CAD_3D_ROOT");
        if (root == null)
            root = new GameObject("Wangsuk_CAD_3D_ROOT");

        GameObject group = GameObject.Find("WALE_SPEC_REVIEW");
        if (group == null)
        {
            group = new GameObject("WALE_SPEC_REVIEW");
            group.transform.SetParent(root.transform, false);
        }

        for (int i = group.transform.childCount - 1; i >= 0; i--)
        {
            Transform child = group.transform.GetChild(i);
            if (child != null)
                DestroyImmediate(child.gameObject);
        }

        List<Vector3> centers = new List<Vector3>();

        foreach (var pf in pfData.entities)
        {
            List<Vector3> pts = ConvertEntityPoints(pf, 0f);
            if (pts == null || pts.Count == 0)
                continue;

            Vector3 sum = Vector3.zero;
            foreach (var p in pts)
                sum += p;

            centers.Add(sum / pts.Count);
        }

        if (centers.Count < 400)
        {
            Debug.LogWarning("WALE_SPEC_REVIEW PF center 부족: " + centers.Count);
            return;
        }

        Vector3 allCenter = Vector3.zero;
        foreach (var c in centers)
            allCenter += c;
        allCenter /= centers.Count;

        Material matSingle = new Material(Shader.Find("Standard"));
        matSingle.color = new Color(1.0f, 0.72f, 0.05f, 1f);

        Material matDouble = new Material(Shader.Find("Standard"));
        matDouble.color = new Color(0.0f, 0.95f, 1.0f, 1f);

        List<WaleSpecRange> specs = GetWaleSpecReviewRanges();

        int created = 0;

        foreach (var spec in specs)
        {
            created += CreateWaleSpecRange(group, centers, allCenter, spec, matSingle, matDouble);
        }

        Debug.Log("========== WALE_SPEC_REVIEW 도면기준 띠장 생성 ==========");
        Debug.Log("기준: C-612~C-619 WALE Spec Review v1");
        Debug.Log("생성 부재 수: " + created);
        Debug.Log("주의: 기존 WALE과 비교하기 위한 검토용 그룹입니다.");
        Debug.Log("색상: 청록=2H 더블띠장 후보, 노랑=H 단띠장 후보");
        Debug.Log("======================================================");
    }

    private List<WaleSpecRange> GetWaleSpecReviewRanges()
    {
        List<WaleSpecRange> list = new List<WaleSpecRange>();

        // C-612 / P001~P067 : 2단
        list.Add(new WaleSpecRange(1, 67, 1, true, "C-612 BAND1"));
        list.Add(new WaleSpecRange(1, 67, 2, true, "C-612 BAND2"));

        // C-613 / P067~P131 : 기본 2단 + P095~P116 부분 3단
        list.Add(new WaleSpecRange(67, 131, 1, true, "C-613 BAND1"));
        list.Add(new WaleSpecRange(67, 131, 2, true, "C-613 BAND2"));
        list.Add(new WaleSpecRange(95, 116, 3, true, "C-613 BAND3"));

        // C-614 / P131~P196 : 기본 2단 + P178~P196 부분 3단
        list.Add(new WaleSpecRange(131, 196, 1, true, "C-614 BAND1"));
        list.Add(new WaleSpecRange(131, 196, 2, true, "C-614 BAND2"));
        list.Add(new WaleSpecRange(178, 196, 3, true, "C-614 BAND3"));

        // C-615 / P196~P248 : 전 구간 3단
        list.Add(new WaleSpecRange(196, 248, 1, true, "C-615 BAND1"));
        list.Add(new WaleSpecRange(196, 248, 2, true, "C-615 BAND2"));
        list.Add(new WaleSpecRange(196, 248, 3, true, "C-615 BAND3"));

        // C-616 / P248~P306 : 기본 2단 + 부분 3단/4단
        list.Add(new WaleSpecRange(248, 306, 1, true, "C-616 BAND1"));
        list.Add(new WaleSpecRange(248, 306, 2, true, "C-616 BAND2"));
        list.Add(new WaleSpecRange(248, 258, 3, true, "C-616 BAND3_A"));
        list.Add(new WaleSpecRange(278, 306, 3, true, "C-616 BAND3_B"));
        list.Add(new WaleSpecRange(248, 251, 4, true, "C-616 BAND4_A"));
        list.Add(new WaleSpecRange(280, 306, 4, true, "C-616 BAND4_B"));

        // C-617 / P306~P365 : 4단 후보
        list.Add(new WaleSpecRange(306, 347, 1, true, "C-617 BAND1"));
        list.Add(new WaleSpecRange(306, 365, 2, true, "C-617 BAND2"));
        list.Add(new WaleSpecRange(306, 365, 3, true, "C-617 BAND3"));
        list.Add(new WaleSpecRange(306, 365, 4, true, "C-617 BAND4"));

        // C-618 / P365~P428 : 복합 4단
        list.Add(new WaleSpecRange(365, 405, 1, true, "C-618 BAND1"));
        list.Add(new WaleSpecRange(365, 428, 2, true, "C-618 BAND2"));
        list.Add(new WaleSpecRange(365, 428, 3, true, "C-618 BAND3"));
        list.Add(new WaleSpecRange(405, 428, 4, true, "C-618 BAND4"));

        // C-619 / P428~P492,P001 : 복합 3단
        list.Add(new WaleSpecRange(428, 475, 1, true, "C-619 BAND1_A"));
        list.Add(new WaleSpecRange(483, 492, 1, true, "C-619 BAND1_B"));
        list.Add(new WaleSpecRange(1, 2, 1, true, "C-619 BAND1_C"));

        list.Add(new WaleSpecRange(428, 475, 2, true, "C-619 BAND2_A"));
        list.Add(new WaleSpecRange(486, 492, 2, true, "C-619 BAND2_B"));
        list.Add(new WaleSpecRange(1, 2, 2, true, "C-619 BAND2_C"));

        list.Add(new WaleSpecRange(428, 469, 3, true, "C-619 BAND3"));

        return list;
    }

    private float GetWaleSpecDepthByBand(int bandIndex)
    {
        // 검토용 깊이값.
        // 최종은 바닥 EL(+30.44/+31.00/+29.54)와 단면도 대조 후 보정.
        if (bandIndex <= 1)
            return 0.6f;

        if (bandIndex == 2)
            return 2.6f;

        if (bandIndex == 3)
            return 4.5f;

        return 5.8f;
    }

    private int CreateWaleSpecRange(GameObject group, List<Vector3> centers, Vector3 allCenter, WaleSpecRange spec, Material matSingle, Material matDouble)
    {
        int created = 0;

        int startPf = Mathf.Clamp(spec.startPf, 1, centers.Count);
        int endPf = Mathf.Clamp(spec.endPf, 1, centers.Count);

        if (endPf <= startPf)
            return 0;

        float depth = GetWaleSpecDepthByBand(spec.bandIndex);

        for (int pfNo = startPf; pfNo < endPf; pfNo++)
        {
            int i0 = Mathf.Clamp(pfNo - 1, 0, centers.Count - 1);
            int i1 = Mathf.Clamp(pfNo, 0, centers.Count - 1);

            Vector3 p0 = centers[i0];
            Vector3 p1 = centers[i1];

            float dist = Vector3.Distance(p0, p1);
            if (dist < 0.03f || dist > 12f)
                continue;

            Vector3 mid = (p0 + p1) * 0.5f;
            Vector3 inward = new Vector3(allCenter.x - mid.x, 0f, allCenter.z - mid.z);

            if (inward.sqrMagnitude > 0.0001f)
                inward.Normalize();
            else
                inward = Vector3.forward;

            string baseName = "WALE_SPEC_" + spec.source + "_P" + pfNo.ToString("000") + "_B" + spec.bandIndex;

            if (spec.doubleH)
            {
                Vector3 offsetA = inward * 0.28f;
                Vector3 offsetB = inward * 0.62f;

                CreateWaleSpecBeam(group, p0, p1, depth, offsetA, matDouble, baseName + "_2H_A");
                CreateWaleSpecBeam(group, p0, p1, depth, offsetB, matDouble, baseName + "_2H_B");
                created += 2;
            }
            else
            {
                Vector3 offset = inward * 0.42f;
                CreateWaleSpecBeam(group, p0, p1, depth, offset, matSingle, baseName + "_H");
                created += 1;
            }
        }

        return created;
    }

    private void CreateWaleSpecBeam(GameObject group, Vector3 p0, Vector3 p1, float depth, Vector3 offset, Material mat, string name)
    {
        Vector3 a = new Vector3(p0.x, -depth, p0.z) + offset;
        Vector3 b = new Vector3(p1.x, -depth, p1.z) + offset;

        Vector3 dir = b - a;
        float len = dir.magnitude;

        if (len < 0.03f)
            return;

        GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Cube);
        obj.name = name;
        obj.transform.SetParent(group.transform, false);
        obj.transform.position = (a + b) * 0.5f;
        obj.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);

        // 길이 방향은 z축. 단면은 검토용 사각 단면.
        obj.transform.localScale = new Vector3(0.18f, 0.16f, len);

        Renderer r = obj.GetComponent<Renderer>();
        if (r != null)
            r.material = mat;
    }
'''

if "private void BuildWaleSpecReviewFromPfCenters" not in text:
    idx = text.rfind("}")
    if idx < 0:
        raise Exception("class 마지막 중괄호를 찾지 못했습니다.")
    text = text[:idx] + helper + "\n" + text[idx:]
    print("WALE_SPEC_REVIEW 함수 추가 완료")
else:
    print("WALE_SPEC_REVIEW 함수 이미 있음")

path.write_text(text, encoding="utf-8")
print("저장 완료")
