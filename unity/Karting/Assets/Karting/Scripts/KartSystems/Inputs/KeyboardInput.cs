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

            // consider no activity if axes value is in [UnpressedValue, UnpressedValue - DeadZone]
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
		    print ("axis_info.HasEverChanged  " + axis_info.HasEverChanged + " set axis =" + axis);
                }
            }
            axis = 0.5F + 0.5F * axis; // convert "centered axes" to "not-centered axes"

            print (string.Format("check {0} > {1}", axis, axis_info.DeadZone));
            bool result = axis > axis_info.DeadZone;
            return result; 
        }

	private float GetTurnAngle() {
            bool setWheelCenter = Input.GetButton("SetWheelCenter");
            float rawHor = (float)Input.GetAxis("Horizontal");
            if (setWheelCenter && rawHor != 1 && rawHor != -1) {
                Debug.Log("setWheelCenter to " + rawHor);
                WheelCenter = rawHor;
            }
            if (rawHor <= -1)
            {
                return -1; // keyboard input
            }
            if (rawHor >= 1)
            {
                return 1; // keyboard output
            }
            
            float turnInput = (rawHor - WheelCenter) * 1.0F;
            return turnInput; // race wheel input
        }

        public override InputData GenerateInput()
        {
            string info = "";
            bool accelerate = CalcAxis(AccelerateButtonName, "Axis 2", Axis2);
            bool brake = CalcAxis(BrakeButtonName, "Axis 3", Axis3);
            float turnInput = GetTurnAngle();

            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3"};
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxisRaw(a));
            }
            info += string.Format("=>accelerate={0},", accelerate);
            info += string.Format("=>brake={0},", brake);
            info += string.Format(",turnInput={0},", turnInput);
            info += string.Format(",WheelCenter={0},", WheelCenter);
            print(info);

            return new InputData
            {
                Accelerate = accelerate,
                //Brake = Input.GetButton(BrakeButtonName),
                Brake = brake,
                TurnInput = turnInput

            };
        }
    }
}
