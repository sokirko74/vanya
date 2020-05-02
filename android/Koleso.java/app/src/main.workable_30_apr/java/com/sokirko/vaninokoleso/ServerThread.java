package com.sokirko.vaninokoleso;

import java.io.IOException;
import java.util.UUID;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.util.Log;
import android.widget.Toast;

public class ServerThread extends Thread {

    private final BluetoothServerSocket bluetoothServerSocket;
    private final CommunicatorService communicatorService;

    public ServerThread(CommunicatorService communicatorService) {
        this.communicatorService = communicatorService;
        final BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        BluetoothServerSocket tmp = null;
        try {
            //tmp = bluetoothAdapter.listenUsingRfcommWithServiceRecord("BluetoothApp", UUID.fromString(MainActivity.UUID));
            tmp = bluetoothAdapter.listenUsingInsecureRfcommWithServiceRecord("BluetoothApp", UUID.fromString(MainActivity.UUID));

        } catch (IOException e) {
            Log.e("ServerThread", e.getLocalizedMessage());

        }
        bluetoothServerSocket = tmp;
    }
    public boolean IsInitialized() {
        return bluetoothServerSocket != null;
    }

    public void run() {

        BluetoothSocket socket = null;

        Log.d("ServerThread", "Started");

        while (true) {
            try {
                socket = bluetoothServerSocket.accept();
            } catch (IOException e) {
                Log.d("ServerThread", "Stop: " + e.getLocalizedMessage());
                break;
            }
            if (socket != null) {
                communicatorService.createCommunicatorThread(socket).startCommunication();
            }
        }
    }

    public void cancel() {
        try {
            if (bluetoothServerSocket != null) {
                bluetoothServerSocket.close();
            }
        } catch (IOException e) {
            Log.d("ServerThread", e.getLocalizedMessage());
        }
    }
}

