using UnityEngine;

namespace KartGame.KartSystems {

    public class KeyboardInput : BaseInput
    {
        public string TurnInputName = "Horizontal";
        public string AccelerateButtonName = "Accelerate";
        public string BrakeButtonName = "Brake";
        
        public override InputData GenerateInput() {
            /*var axis = new string[] { "Horizontal", "Vertical", "Accelerate", "Axis 1", "Axis 2", "Axis 3" };
            string info = "";
            foreach (string a in axis)
            {

                info += string.Format("{0}={1},", a, Input.GetAxis(a));
            }
            print(info);*/
            bool accelerate = Input.GetButton(AccelerateButtonName);
            float vertical = Input.GetAxis("Vertical");
            if (vertical > -0.98 && vertical != 0)
            {
                accelerate = true;
            }

            return new InputData
            {
                Accelerate = accelerate,
                Brake = Input.GetButton(BrakeButtonName),
                TurnInput = Input.GetAxis("Horizontal")
               
            };
        }
    }
}
