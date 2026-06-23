

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;
package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();
package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
               

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;
package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();
package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @peech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;
package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();
package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @peech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}
= results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}

            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}
= results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}
     Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @peech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches package com.rj.assistant;

import android.Manifest;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView tvResult;
    private Button btnSpeak;
    private TextToSpeech tts;
    private SpeechRecognizer speechRecognizer;
    private AudioManager audioManager;

    private static final int PERMISSION_REQUEST_RECORD_AUDIO = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}
= results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvResult = findViewById(R.id.tvResult);
        btnSpeak = findViewById(R.id.btnSpeak);
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);

        checkMicPermission();

        // APP KHULTE HI LANGUAGE POP-UP AAYEGA
        showLanguageSetupPopup();

        // TTS SETUP (Echo Fix ke sath)
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.setPitch(1.1f);
                tts.setSpeechRate(0.95f);

                // ECHO FIX: Jab AI bolega, toh Mic button band ho jayega
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(false);
                            btnSpeak.setText("JARVIS BOL RAHA HAI...");
                        });
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }

                    @Override
                    public void onError(String utteranceId) {
                        runOnUiThread(() -> {
                            btnSpeak.setEnabled(true);
                            btnSpeak.setText("TAP TO SPEAK");
                        });
                    }
                });
            }
        });

        // SPEECH RECOGNIZER SETUP (Bina Beep Sound ke)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Sun raha hoon...");
            }
            @Override
            public void onBeginningOfSpeech() {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
            @Override
            public void onEndOfSpeech() {
                tvResult.setText("Processing...");
            }
            @Override
            public void onError(int error) {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
                tvResult.setText("Mic Error Code: " + error);
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String spokenText = matches.get(0);
                    tvResult.setText("Aapne kaha: " + spokenText);
                    
                    tts.speak("Aapne kaha, " + spokenText, TextToSpeech.QUEUE_FLUSH, null, "tts_id");
                }
            }
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        btnSpeak.setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "hi-IN"); 
                intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true); 
                
                // MIC BEEP SOUND MUTE KARNE WALA TRICK
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0);
                
                speechRecognizer.startListening(intent);
            } else {
                checkMicPermission();
            }
        });
    }

    private void showLanguageSetupPopup() {
        new AlertDialog.Builder(this)
            .setTitle("Offline Language Setup")
            .setMessage("Kya aap Offline kaam karne ke liye Hindi/English language pack free mein download karna chahte hain?")
            .setPositiveButton("Haan (Download)", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Intent installIntent = new Intent();
                    installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                    startActivity(installIntent);
                    Toast.makeText(MainActivity.this, "Yahan se apni language download kar lein!", Toast.LENGTH_LONG).show();
                }
            })
            .setNegativeButton("Baad Mein", null)
            .show();
    }

    private void checkMicPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION_REQUEST_RECORD_AUDIO);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_RECORD_AUDIO && grantResults.length > 0) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Mic ready!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permission zaroori hai!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) { tts.stop(); tts.shutdown(); }
        if (speechRecognizer != null) { speechRecognizer.destroy(); }
        if (audioManager != null) {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0);
        }
        super.onDestroy();
    }
}
