using UnityEngine;

namespace KartGame.KartSystems
{

    public class KeyboardInput : BaseInput
    {
        public static bool Axis2HasChanged = false;
        public string TurnInputName = "Horizontal";
        public string AccelerateButtonName = "Accelerate";
        public string BrakeButtonName = "Brake";

        public override InputData GenerateInput()
        {
            string info = "";
            bool accelerate = Input.GetButton(AccelerateButtonName);
            info += string.Format("accelerate btn={0},", accelerate);
            float axis2 = Input.GetAxisRaw("Axis 2");
            const float axis2Unpressed = 1;
            const float axis2Uninitialized = 0; 
            const float axis2DeadZone = 0.05F; 

            if (!Application.isFocused) {
                axis2 =  axis2Uninitialized;
                Axis2HasChanged = false; // as if in the beginning
            }

            if (!Axis2HasChanged) {
                if (axis2 != axis2Uninitialized) {
                    Axis2HasChanged = true;
                } 
                else  {
                    axis2 = axis2Unpressed; // convert null to normal unpressed value
                }
            }
            if (!accelerate) { // no keyboard

                print(string.Format("check {0} < {1}", axis2, (axis2Unpressed - axis2DeadZone)));
                accelerate = axis2 < (axis2Unpressed - axis2DeadZone);
            } else  {
                print("keyboard accelerating");
            }

                
            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3"};
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxisRaw(a));
            }
            info += string.Format("=>accelerate={0},", accelerate);
            info += string.Format(",Axis2HasChanged={0},", Axis2HasChanged);
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
                Brake = Input.GetButton(BrakeButtonName),
                //Brake = false,
                TurnInput = turnInput

            };
        }
    }
}
