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
            bool accelerate = Input.GetButton(AccelerateButtonName);
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
            if (axis2 > -0.98)
            {
                accelerate = true;
            }
            //accelerate = false;
            string info = "";
            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3"};
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxis(a));
            }
            var btns = new string[] { "LeftWheelButton" };
            foreach (string a in btns)
            {

                info += string.Format("{0}={1},", a, Input.GetButton(a));
            }

            info += string.Format("=>pedal={0},", accelerate);
            info += string.Format(",GlobalStarted={0},", GlobalStarted);

            print(info);

            return new InputData
            {
                Accelerate = accelerate,
                //Brake = Input.GetButton(BrakeButtonName),
                Brake = false,
                TurnInput = Input.GetAxis("Horizontal")

            };
        }
    }
}
