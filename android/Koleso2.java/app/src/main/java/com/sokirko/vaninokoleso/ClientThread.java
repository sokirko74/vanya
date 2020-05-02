package com.sokirko.vaninokoleso;

import java.io.IOException;
import java.io.OutputStream;
import java.lang.reflect.InvocationTargetException;
import java.util.UUID;
import java.lang.reflect.Method;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.util.Log;
import android.widget.Toast;

public class ClientThread extends Thread {

    private volatile Communicator communicator;

    private BluetoothSocket m_Socket = null;
    private BluetoothAdapter bluetoothAdapter;
    private final CommunicatorService communicatorService;


    public ClientThread(BluetoothDevice device, CommunicatorService communicatorService) {

        this.communicatorService = communicatorService;
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();

        try {
            m_Socket = device.createInsecureRfcommSocketToServiceRecord(UUID.fromString(MainActivity.UUID));
        } catch (IOException e) {
            Log.d("ClientThread", e.getLocalizedMessage());
            return;
        }

        bluetoothAdapter.cancelDiscovery();

        try {
            m_Socket.connect();
        } catch (IOException e) {
            // second retry
            try {
                Log.d("ClientThread", "second retry of socket connect");
                m_Socket.connect();
            } catch (IOException e2) {
                Log.d("ClientThread", e2.getLocalizedMessage());
                try {
                    m_Socket.close();
                    m_Socket = null;
                } catch (IOException e3) {
                    Log.d("ClientThread", e3.getLocalizedMessage());
                }
            }
            Log.d("ClientThread", e.getLocalizedMessage());
        }
        if (m_Socket != null) {
            Log.d("ClientThread", "Connected");
        }

    }

    public synchronized Communicator getCommunicator() {
        return communicator;
    }

    public boolean IsInitialized() {
        return m_Socket != null;
    }

    public void run() {
        if (m_Socket == null) {
            return;
        }
        try {
            synchronized (this) {
                communicator = communicatorService.createCommunicatorThread(m_Socket);
            }
            new Thread(new Runnable() {
                @Override
                public void run() {
                    Log.d("ClientThread", "Start");
                    communicator.startCommunication();
                }
            }).start();
        } catch (Exception e) {
            try {
                m_Socket.close();
            } catch (IOException closeException) {
                Log.d("ClientThread", closeException.getLocalizedMessage());
            }
        }
    }

    public void cancel() {
        if (communicator != null) communicator.stopCommunication();
    }
}