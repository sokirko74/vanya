using UnityEngine;

namespace KartGame.KartSystems {

    public class KeyboardInput : BaseInput
    {
        public string TurnInputName = "Horizontal";
        public string AccelerateButtonName = "Accelerate";
        public string BrakeButtonName = "Brake";
        
        public override InputData GenerateInput() {
            bool accelerate = Input.GetButton(AccelerateButtonName);
            float vertical = Input.GetAxis("Vertical");
            if (vertical > -0.98 && vertical != 0)
            {
                accelerate = true;
            }
            //accelerate = false;
            var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3" };
            string info = "";
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxis(a));
            }

            info += string.Format("=>pedal={0},", accelerate);
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
