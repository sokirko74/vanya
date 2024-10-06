using TMPro;
using UnityEngine;
using UnityEngine.Animations;

namespace KartGame.KartSystems
{
    public struct AxisInfo
    {
    	    // IMPORTANT!! All axis are not "inverted" in Unity Project Settings.
    	    // but wheel pedals are treated as the main wheel (so 0 is in the center position)
    	    
            // UninitializedValue is returned in the beginning before any activity, null value 
            public const float UninitializedValue = 0;  

            // UnpressedValue is returned during playing if the pedal is unpressed
            public const float UnpressedValue = -1;  

            // consider no activity if axes value is in [0, DeadZone]
            public float DeadZone; 

            // there was some activity for this axes
            public bool HasEverChanged;

            public AxisInfo( float deadZone) {
                DeadZone = deadZone;
                HasEverChanged = false;
            }
    }


    public class KeyboardInput : BaseInput
    {
        public static AxisInfo Axis2;
        public static AxisInfo Axis3;
        public string TurnInputName = "Horizontal";
        public string AccelerateButtonName = "Accelerate";
        public string BrakeButtonName = "Brake";

        public float WheelCenter = 0.0F;

        static KeyboardInput()
        {
        	
            Axis2 = new AxisInfo(0.05F);
            Axis3 = new AxisInfo(0.5F);// special for Vanya
        }

	private bool CalcAxis(string btnName, string axisName, AxisInfo axis_info)
        {
            if (Input.GetButton(btnName)) {
            	return true; // keyboard input
            }
            float axis = Input.GetAxis(axisName);
            if (!Application.isFocused) {
                axis =  AxisInfo.UninitializedValue;
                axis_info.HasEverChanged = false; // as if in the beginning
            }

            if (!axis_info.HasEverChanged) {
                if (axis != AxisInfo.UninitializedValue) {
                    axis_info.HasEverChanged = true;
                } 
                else  {
                    axis = AxisInfo.UnpressedValue; // convert null to normal unpressed value
		            //print ("axis_info.HasEverChanged  " + axis_info.HasEverChanged + " set axis =" + axis);
                }
            }
            axis = (axis + 1.0F ) / 2.0F; // convert "centered axes" to "not-centered axes" [-1, 1] -> [0, 1]

            //print (string.Format("check {0} > {1}", axis, axis_info.DeadZone));
            bool result = axis > axis_info.DeadZone;
            return result; 
        }

	private float GetTurnAngle() {
            float horiz = (float)Input.GetAxis("Horizontal");
            if (horiz == -1)
            {
                return -1; // keyboard input
            }
            if (horiz == 1)
            {
                return 1; // keyboard input
            }
            if (Input.GetButton("SetWheelCenter")) {
                Debug.Log("setWheelCenter to " + horiz);
                WheelCenter = horiz;
            }       
            float turnInput = horiz - WheelCenter;
            return turnInput; // race wheel input
        }

        private void printState(InputData inputData) {
            string info = "";
            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3"};
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxisRaw(a));
            }
            info += string.Format("=>accelerate={0},", inputData.Accelerate);
            info += string.Format("=>brake={0},", inputData.Brake);
            info += string.Format(",turnInput={0},", inputData.TurnInput);
            info += string.Format(",WheelCenter={0},", WheelCenter);
            print(info);
        }

        public override InputData GenerateInput()
        {
            var inputData = new InputData
            {
                Accelerate = CalcAxis(AccelerateButtonName, "Axis 2", Axis2),
                Brake = CalcAxis(BrakeButtonName, "Axis 3", Axis3),
                TurnInput = GetTurnAngle()

            };
            //printState(inputData);
            return inputData;
        }
    }
}
