using System;
using System.Collections;
using System.Collections.Generic;
using Google.Protobuf.WellKnownTypes;
using UnityEngine;




[Serializable]
public class RedLightSwitch : MonoBehaviour
{
    public Light RedLight;
    public Light YellowLight;
    public Light GreenLight;

    // Start is called before the first frame update
    public void Start()
    {
        Debug.Log("TrafficLightSwitch.Start");
        Debug.Log("RedLight.enabled=" + RedLight.enabled);
        RedLight.enabled = false;
        YellowLight.enabled = false;
        GreenLight.enabled = false;
    }

    // Update is called once per frame
    public void Update()
    {
        long unixTimestamp = (long)DateTime.Now.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
        long p = unixTimestamp % 5;
        if (p < 2) {
            RedLight.enabled = true;
            YellowLight.enabled = false;
            GreenLight.enabled = false;
        }
        else if (p < 3) {
            RedLight.enabled = false;
            YellowLight.enabled = true;
            GreenLight.enabled = false;
        } else {
            RedLight.enabled = false;
            YellowLight.enabled = false;
            GreenLight.enabled = true;
        }
        Debug.Log("lights" + RedLight.enabled + YellowLight.enabled + GreenLight.enabled);

    }
}


// public class RedLightSwitch : MonoBehaviour
// {
//     public Light RedLight;
//     public Light YellowLight;
//     public Light GreenLight;

//     // Start is called before the first frame update
//     public void Start()
//     {
//         //RedLight = new Light();
//         //YellowLight = new Light();
//         //GreenLight = new Light();

//         Debug.Log("TrafficLightSwitch.Start");
//     }

//     // Update is called once per frame
//     public void Update()
//     {
//         long unixTimestamp = (long)DateTime.Now.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
//         long p = unixTimestamp % 50;
//         if (p < 10) {
//             RedLight.enabled = true;
//             YellowLight.enabled = false;
//             GreenLight.enabled = false;
//         }
//         else if (10 <= p &&  p < 30) {
//             RedLight.enabled = false;
//             YellowLight.enabled = true;
//             GreenLight.enabled = false;
//         } else {
//             RedLight.enabled = false;
//             YellowLight.enabled = false;
//             GreenLight.enabled = true;

//         }
//     }
// }
