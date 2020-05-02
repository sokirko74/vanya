package com.sokirko.vaninokoleso;

import android.os.Bundle;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.TextView;
import java.io.File;
import java.util.Set;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.AsyncTask;
import android.os.Environment;
import android.util.Log;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;
import android.app.ListActivity;
import android.app.ProgressDialog;
import android.media.MediaPlayer;

//public class MainActivity extends AppCompatActivity {
public class MainActivity extends ListActivity {

    private final static int REQUEST_ENABLE_BT = 1;
    private File[] m_AudioFiles;
    private int m_AudioFileNo = -1;
    private int m_SwitchNo = -1;
    private int m_SwitchesCount = 4;
    MediaPlayer m_MediaPlayer = null;

    //public final static String UUID = "3647e4a0-2bac-11e7-9598-0800200c9a66";

    // http://stackoverflow.com/questions/4632524/how-to-find-the-uuid-of-serial-port-bluetooth-device
    public static final String UUID = "00001101-0000-1000-8000-00805f9b34fb";

    private BluetoothAdapter m_BluetoothAdapter;
    private BroadcastReceiver discoverDevicesReceiver;
    private BroadcastReceiver discoveryFinishedReceiver;

    private List<BluetoothDevice> m_DiscoveredDevices = new ArrayList<BluetoothDevice>();

    private ArrayAdapter<BluetoothDevice> m_ListAdapter;
    private TextView m_Console;


    private ProgressDialog progressDialog;

    private ClientThread clientThread;

    private final CommunicatorService communicatorService = new CommunicatorService() {
        @Override
        public Communicator createCommunicatorThread(BluetoothSocket socket) {
            return new CommunicatorImpl(socket, new CommunicatorImpl.CommunicationListener() {
                @Override
                public void onMessage(final String message) {
                    runOnUiThread(new Runnable() {
                                      @Override
                                      public void run() {
                                          m_Console.append(message + "\n");
                                          if (message.startsWith("switch")) {
                                              PlayAudio(Integer.parseInt(message.substring(6)));
                                          }
                                      }
                                  }
                    );
                }
            });
        }
    };

    void ShowMessage(String mess, int duration) {
        Toast.makeText(this, mess, Toast.LENGTH_LONG).show();
        AddToConsole(mess);
    }

    public void AddToConsole(String mess) {
        String text  = m_Console.getText().toString();
        if (text.length() > 200) {
            text = text.substring(text.length() - 200);
        }
        m_Console.setText(text + mess);
    }

    public File GetAudioTrack (int new_switch_no) {
        if (new_switch_no == m_SwitchNo) {
            return null;
        }
        if (m_SwitchNo < new_switch_no) {
            m_AudioFileNo++;
            if (m_AudioFileNo >= m_AudioFiles.length) {
                m_AudioFileNo = 0;
            }
        }
        else
        if (m_SwitchNo > new_switch_no || ( m_SwitchNo <=0 && new_switch_no == m_SwitchesCount - 1 ) ) {
            m_AudioFileNo--;
            if (m_AudioFileNo < 0) {
                m_AudioFileNo = m_AudioFiles.length - 1;
            }
        }
        AddToConsole ("Get reed N " + Integer.toString(new_switch_no) + "  set audio N "+ Integer.toString(m_AudioFileNo) + "\n");
        AddToConsole ("Play " + m_AudioFiles[m_AudioFileNo].getAbsolutePath()  + "\n");
        m_SwitchNo = new_switch_no;
        return m_AudioFiles[m_AudioFileNo];
    }

    public void StopAudio(View view) {
        if (m_MediaPlayer.isPlaying()) {
            m_MediaPlayer.stop();
        }
        m_MediaPlayer.release();
        m_MediaPlayer.reset();

    }

    public void PlayAudio (int new_switch_no)    {
        StopAudio(null);

        File AudioTrack = GetAudioTrack (new_switch_no);
        if (AudioTrack == null) {
            return;
        }

        try {
            m_MediaPlayer.setDataSource(AudioTrack.getAbsolutePath());
        }
        catch (Exception e) {
            AddToConsole ("Cannot find file " + AudioTrack.getAbsolutePath() + "\n");
            return;
        }
        try {
            m_MediaPlayer.prepare();
            m_MediaPlayer.getDuration();
            m_MediaPlayer.start();
        }
        catch (Exception e) {
            AddToConsole ("Cannot play file\n");
        }
    }

    public boolean ReadAudioFileNames (File data_dir) {
        AddToConsole("Search files in: " + data_dir.getAbsolutePath() + "\n");
        m_AudioFiles = data_dir.listFiles();
        if ((m_AudioFiles != null) && (m_AudioFiles.length > 0)) {
            AddToConsole("Number of found audio files: " + m_AudioFiles.length + "\n");
            return true;
        }
        else {
            AddToConsole("No files to play\n");
            return false;
        }

    }

    public void ConnectDevice( BluetoothDevice device) {
        ShowMessage("Try to connect to " + device.getName() + "...\n", 3);
        if (clientThread != null) {
            clientThread.cancel();
        }

        clientThread = new ClientThread(device, communicatorService);
        String message;
        if (clientThread.IsInitialized()) {
            clientThread.start();
            message = "Connection is established";
        } else {
            message = "Cannot make connection";
        }
        ShowMessage(message, 2);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
        m_Console = (TextView) findViewById(R.id.data_text);

        if (!ReadAudioFileNames(getFilesDir())) {
            ReadAudioFileNames(getExternalFilesDir(Environment.getDataDirectory().getAbsolutePath()));
        }

        m_BluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (!m_BluetoothAdapter.isEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
        }
        BluetoothDevice hc06 = m_BluetoothAdapter.getRemoteDevice("20:16:05:23:17:28");
        if (hc06 != null) {
            m_DiscoveredDevices.add(hc06);
            ConnectDevice( hc06 );
        }
        
        m_ListAdapter = new ArrayAdapter<BluetoothDevice>(getBaseContext(), android.R.layout.simple_list_item_1, m_DiscoveredDevices) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                View view = super.getView(position, convertView, parent);
                final BluetoothDevice device = getItem(position);
                ((TextView) view.findViewById(android.R.id.text1)).setText(device.toString());
                return view;
            }
        };
        setListAdapter(m_ListAdapter);
        m_ListAdapter.notifyDataSetChanged();
        m_MediaPlayer = new MediaPlayer();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    public void discoverDevices(View view) {

        m_DiscoveredDevices.clear();
        m_ListAdapter.notifyDataSetChanged();

        if (discoverDevicesReceiver == null) {
            discoverDevicesReceiver = new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    String action = intent.getAction();

                    if (BluetoothDevice.ACTION_FOUND.equals(action)) {
                        BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);

                        if (!m_DiscoveredDevices.contains(device)) {
                            m_DiscoveredDevices.add(device);
                            m_ListAdapter.notifyDataSetChanged();
                        }
                    }
                }
            };
        }

        if (discoveryFinishedReceiver == null) {
            discoveryFinishedReceiver = new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    getListView().setEnabled(true);
                    if (progressDialog != null)
                        progressDialog.dismiss();
                    ShowMessage("Поиск закончен. Выберите устройство для отправки ообщения.", Toast.LENGTH_SHORT);
                    unregisterReceiver(discoveryFinishedReceiver);
                }
            };
        }

        registerReceiver(discoverDevicesReceiver, new IntentFilter(BluetoothDevice.ACTION_FOUND));
        registerReceiver(discoveryFinishedReceiver, new IntentFilter(BluetoothAdapter.ACTION_DISCOVERY_FINISHED));

        getListView().setEnabled(false);

        progressDialog = ProgressDialog.show(this, "Поиск устройств", "Подождите...");

        m_BluetoothAdapter.startDiscovery();
    }

    @Override
    public void onPause() {
        super.onPause();
        m_BluetoothAdapter.cancelDiscovery();
    }

    @Override
    public void onResume() {
        super.onResume();
    }

    public void onListItemClick(ListView parent, View v,
                                int position, long id) {
        ConnectDevice( m_DiscoveredDevices.get(position));
    }


}
