package com.sokirko.vaninokoleso;

import android.os.Bundle;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.TextView;
import java.io.File;
import java.io.FilenameFilter;
import java.util.Arrays;
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
    private File m_AudioAlbumsDir;
    private final int MaxConsoleLen = 500;

    //public final static String UUID = "3647e4a0-2bac-11e7-9598-0800200c9a66";

    // http://stackoverflow.com/questions/4632524/how-to-find-the-uuid-of-serial-port-bluetooth-device
    public static final String UUID = "00001101-0000-1000-8000-00805f9b34fb";

    private BluetoothAdapter m_BluetoothAdapter;
    private BluetoothDevice m_Device;
    private TextView m_Console;

    private ArrayList<String> m_AudioAlbums = new ArrayList<String>();
    private ArrayAdapter<String> m_ListAdapter;





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
        if (text.length() > MaxConsoleLen) {
            text = text.substring(text.length() - MaxConsoleLen);
        }
        m_Console.setText(text + mess + "\n");
    }

    public File GetAudioTrack (int new_switch_no) {
        if (new_switch_no == m_SwitchNo) {
            return null;
        }

        if (m_SwitchNo <=0 && new_switch_no == m_SwitchesCount - 1 ) { // 0 -> last
            m_AudioFileNo--;
        }
        else if (m_SwitchNo  == m_SwitchesCount - 1 && new_switch_no == 0 ) { // last ->  0
            m_AudioFileNo++;
        }
        else if (m_SwitchNo < new_switch_no) {
            m_AudioFileNo++;
        }
        else if (m_SwitchNo > new_switch_no) {
            m_AudioFileNo--;
        }

        if (m_AudioFileNo >= m_AudioFiles.length) {
            m_AudioFileNo = 0;
        }
        if (m_AudioFileNo < 0) {
            m_AudioFileNo = m_AudioFiles.length - 1;
        }
        AddToConsole ("Get reed N " + Integer.toString(new_switch_no) + "  set audio N "+ Integer.toString(m_AudioFileNo));
        AddToConsole ("Play " + m_AudioFiles[m_AudioFileNo].getAbsolutePath());
        m_SwitchNo = new_switch_no;
        return m_AudioFiles[m_AudioFileNo];
    }

    public void StopAudio(View view) {
        if (m_MediaPlayer.isPlaying()) {
            m_MediaPlayer.stop();
        }
        //m_MediaPlayer.release();
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
            AddToConsole ("Cannot find file " + AudioTrack.getAbsolutePath());
            return;
        }
        try {
            m_MediaPlayer.prepare();
            m_MediaPlayer.getDuration();
            m_MediaPlayer.start();
        }
        catch (Exception e) {
            AddToConsole ("Cannot play file");
        }
    }

    public boolean ReadAudioFileNames (String album_name) {
        File data_dir = new File(m_AudioAlbumsDir + "/" + album_name);
        AddToConsole("Search files in: " + data_dir.getAbsolutePath());
        m_AudioFiles = data_dir.listFiles();
        if ((m_AudioFiles != null) && (m_AudioFiles.length > 0)) {
            AddToConsole("Number of found audio files: " + m_AudioFiles.length);
            return true;
        }
        else {
            AddToConsole("No files to play");
            return false;
        }

    }

    public void ConnectDevice( BluetoothDevice device) {
        ShowMessage("Try to connect to " + device.getName() + "...", 3);
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
        setContentView(R.layout.activity_main);
        m_Console = findViewById(R.id.data_text);
        m_AudioAlbumsDir = getExternalFilesDir(Environment.getDataDirectory().getAbsolutePath());
        String[] files = m_AudioAlbumsDir.list(new FilenameFilter() {
            @Override
            public boolean accept(File current, String name) {
                return new File(current, name).isDirectory();
            }
        });
        m_AudioAlbums = new ArrayList<String>(Arrays.asList(files));
        if (m_AudioAlbums.size() > 0)
            ReadAudioFileNames(m_AudioAlbums.get(0));

        m_BluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (m_BluetoothAdapter == null) {
            ShowMessage("cannot find bluetooth adapter", 10);
            System.exit(1);
        }
        if (!m_BluetoothAdapter.isEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
        }
        m_Device = m_BluetoothAdapter.getRemoteDevice("20:16:05:23:17:28");
        if (m_Device != null) {
            ConnectDevice( m_Device );
        }
        else {
            ShowMessage("Cannot find bluetooth device", 3);
        }

        m_MediaPlayer = new MediaPlayer();

        m_ListAdapter = new ArrayAdapter<String>(getBaseContext(), android.R.layout.simple_list_item_1, m_AudioAlbums) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                View view = super.getView(position, convertView, parent);
                ((TextView) view.findViewById(android.R.id.text1)).setText(getItem(position));
                return view;
            }
        };
        setListAdapter(m_ListAdapter);
        m_ListAdapter.notifyDataSetChanged();
        getListView().setItemChecked(0, true);
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

    public void ReconnectDevice(View view) {
        ConnectDevice( m_Device );
    }

    @Override
    public void onPause() {
        super.onPause();
    }

    @Override
    public void onResume() {
        super.onResume();
    }

    public void onListItemClick(ListView parent, View v,
                                int position, long id) {
        ReadAudioFileNames (m_AudioAlbums.get(position));
    }


}
