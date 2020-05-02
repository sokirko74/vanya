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
            //createInsecureRfcommSocketToServiceRecord
            bluetoothAdapter.cancelDiscovery();
            m_Socket.connect();
        } catch (IOException e) {
            if (m_Socket != null) {
                try {
                    m_Socket.close();
                    m_Socket = null;
                } catch (IOException e2) {
                    Log.d("ClientThread", e2.getLocalizedMessage());
                }
            }
            Log.d("ClientThread", e.getLocalizedMessage());
        }
/*

        try{

            //Инициируем соединение с устройством
            Method m = device.getClass().getMethod(
                    //"createRfcommSocket", new Class[] {int.class});
                    "createInsecureRfcommSocket", new Class[] {int.class});
            m_Socket = (BluetoothSocket) m.invoke(device, 1);
           bluetoothAdapter.cancelDiscovery();
           m_Socket.connect();

            //В случае появления любых ошибок, выводим в лог сообщение
        } catch (IOException e) {
            Log.d("BLUETOOTH", e.getMessage());
        } catch (SecurityException e) {
            Log.d("BLUETOOTH", e.getMessage());
        } catch (NoSuchMethodException e) {
            Log.d("BLUETOOTH", e.getMessage());
        } catch (IllegalArgumentException e) {
            Log.d("BLUETOOTH", e.getMessage());
        } catch (IllegalAccessException e) {
            Log.d("BLUETOOTH", e.getMessage());
        } catch (InvocationTargetException e) {
            Log.d("BLUETOOTH", e.getMessage());
        }
*/
        Log.d("ClientThread", "Connected");

    }

    public synchronized Communicator getCommunicator() {
        return communicator;
    }

    public boolean IsInitialized() {
        return m_Socket != null;
    }

    public void run() {
        bluetoothAdapter.cancelDiscovery();
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