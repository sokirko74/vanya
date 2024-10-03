using UnityEngine;

namespace KartGame.KartSystems
{

    public class KeyboardInput : BaseInput
    {
        public static bool GlobalStarted = false;
        public string TurnInputName = "Horizontal";
        public string AccelerateButtonName = "Accelerate";
        public string BrakeButtonName = "Brake";

        public override InputData GenerateInput()
        {
            string info = "";
            bool accelerate = Input.GetButton(AccelerateButtonName);
            info += string.Format("accelerate btn={0},", accelerate);
            float axis2 = Input.GetAxis("Axis 2");
            if (!GlobalStarted)
            {
                if (axis2 != 0)
                {
                    GlobalStarted = true;
                }
                else
                {
                    axis2 = -1;
                }
            }
            if (axis2 > -0.95)
            {
                accelerate = true;
            }
            //accelerate = false;
            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3"};
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxis(a));
            }
            info += string.Format("=>accelerate={0},", accelerate);
            info += string.Format(",GlobalStarted={0},", GlobalStarted);
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
