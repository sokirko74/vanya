using TMPro;
using UnityEngine;


public class TopSpeedDropDown : MonoBehaviour {
    [SerializeField] private TMP_Dropdown dropdown;

    public void OnDropDownChanged() {
        string v = dropdown.options[dropdown.value].text;
        Debug.Log("top speed = " + v);
    }
}
