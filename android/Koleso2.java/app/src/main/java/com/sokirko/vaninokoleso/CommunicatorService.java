package com.sokirko.vaninokoleso;

import android.bluetooth.BluetoothSocket;

interface CommunicatorService {
    Communicator createCommunicatorThread(BluetoothSocket socket);
}
