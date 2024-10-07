using TMPro;
using UnityEngine;


public class TopSpeedDropDown : MonoBehaviour {
    [SerializeField] private TMP_Dropdown dropdown;
    public static int UserTopSpeed = 2;

    public void Start( ) {
        Debug.Log("TopSpeedDropDown start");
        dropdown.onValueChanged.AddListener(delegate {
            OnDropDownChanged();

        });
    }

    public void OnDropDownChanged() {
        string v = dropdown.options[dropdown.value].text;
        Debug.Log("top speed = " + v);
        UserTopSpeed = int.Parse(v);
    }
}
