package com.sokirko.vaninokoleso;

import java.io.IOException;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.OutputStream;
import java.io.InputStreamReader;

import android.bluetooth.BluetoothSocket;
import android.util.Log;

public class CommunicatorImpl extends Thread implements Communicator {

    interface CommunicationListener {
        void onMessage(String message);
    }
    private final BluetoothSocket socket;
    private final BufferedReader  inputStream;
    private final CommunicationListener listener;

    public CommunicatorImpl(BluetoothSocket socket, CommunicationListener listener) {
        this.socket = socket;
        this.listener = listener;
        InputStream tmpIn = null;
        try {
            tmpIn = socket.getInputStream();
        } catch (IOException e) {
            Log.d("CommunicatorImpl", e.getLocalizedMessage());
        }
        inputStream = new BufferedReader(new InputStreamReader(tmpIn));
    }

    @Override
    public void startCommunication() {
        byte[] buffer = new byte[32];

        int bytes;

        Log.d("CommunicatorImpl", "Run the communicator");

        while (true) {
            try {
                //bytes = inputStream.read(buffer);
                String line = inputStream.readLine();
                //Log.d("CommunicatorImpl", "Read " + bytes + " bytes");
                if (listener != null) {
                    //listener.onMessage(new String(buffer).substring(0, bytes));
                    listener.onMessage(line);
                }
            } catch (IOException e) {
                Log.d("CommunicatorImpl", e.getLocalizedMessage());
                break;
            }
        }
    }

    @Override
    public void stopCommunication() {
        try {
            socket.close();
        } catch (IOException e) {
            Log.d("CommunicatorImpl", e.getLocalizedMessage());
        }
    }

}