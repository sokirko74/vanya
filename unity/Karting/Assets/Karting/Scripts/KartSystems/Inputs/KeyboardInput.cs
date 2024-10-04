using UnityEngine;
using UnityEngine.Animations;

namespace KartGame.KartSystems
{
    public struct AxisInfo
    {
            // UninitializedValue is returned in the beginning before any activity, null value 
            public float UninitializedValue;  

            // UnpressedValue is returned during playing if the pedal is unpressed
            public float UnpressedValue;  

            // consider no activity if axes value is in [UnpressedValue, UnpressedValue - DeadZone]
            public float DeadZone; 

            // there was some activity for this axes
            public bool HasEverChanged;

            public AxisInfo(float uninitializedValue, float unpressedValue, float deadZone) {
                UninitializedValue = uninitializedValue;
                UnpressedValue = unpressedValue;
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

        static KeyboardInput()
        {
            Axis2 = new AxisInfo(0, 1, 0.05F);
            Axis3 = new AxisInfo(0, -1, 0.7F);// special for Vanya
        }
        public bool CalcAxis(string btnName, string axisName, AxisInfo axis_info)
        {
            bool result = Input.GetButton(btnName);
            float axis = Input.GetAxisRaw(axisName);
            if (!Application.isFocused) {
                axis =  axis_info.UninitializedValue;
                axis_info.HasEverChanged = false; // as if in the beginning
            }

            if (!axis_info.HasEverChanged) {
                if (axis != axis_info.UninitializedValue) {
                    axis_info.HasEverChanged = true;
                } 
                else  {
                    axis = axis_info.UnpressedValue; // convert null to normal unpressed value
                }
            }
            if (!result) { // no keyboard
                if (axis_info.UnpressedValue > 0) {
                    result = axis < (axis_info.UnpressedValue - axis_info.DeadZone);
                }
                else {
                    //print (string.Format("check {0} > {1} + {2}", axis, axis_info.UnpressedValue, axis_info.DeadZone));
                    result = axis > (axis_info.UnpressedValue + axis_info.DeadZone);
                }
            } 
            return result;
        }

        public override InputData GenerateInput()
        {
            string info = "";
            bool accelerate = CalcAxis(AccelerateButtonName, "Axis 2", Axis2);
            bool brake = CalcAxis(BrakeButtonName, "Axis 3", Axis3);
            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3"};
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxisRaw(a));
            }
            info += string.Format("=>accelerate={0},", accelerate);
            info += string.Format("=>brake={0},", brake);
            info += string.Format(",Application.isFocused={0},", Application.isFocused);
            float turnInput = (float)(Input.GetAxis("Horizontal") * 0.9);
            if (turnInput < -1)
            {
                turnInput = -1;
            }
            if (turnInput > 1)
            {
                turnInput = 1;
            }
            info += string.Format(",turnInput={0},", turnInput);

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
