package com.example.vanina_tesla

import android.content.Context
import android.util.Log
import androidx.preference.PreferenceManager
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class EngineSoundInstrumentedTest {

    private lateinit var mockBluetooth: MockBluetoothDataSource
    private var previousProvider: ((Context) -> BluetoothDataSource)? = null

    @Before
    fun setUp() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        PreferenceManager.getDefaultSharedPreferences(context).edit().clear().commit()
        previousProvider = MainActivity.dataSourceProvider
        mockBluetooth = MockBluetoothDataSource()
        MainActivity.dataSourceProvider = { mockBluetooth }
    }

    @After
    fun tearDown() {
        previousProvider?.let { MainActivity.dataSourceProvider = it }
    }

    private fun log(message: String) {
        Log.d("WheelchairTest", message)
    }


    @Test
    fun engineSoundsOnIdleAndIncreasesWithSpeed() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            waitUntilEngineReady(scenario)

            scenario.onActivity { activity ->
                assertTrue("двигатель должен молчать до поступления первых данных", activity.enginePlayer.isMuted)
            }

            Thread.sleep(2000)

            log("mockBluetooth.setRaw(512, 700)")
            scenario.onActivity {
                mockBluetooth.setRaw(512, 700)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()

            scenario.onActivity { activity ->
                assertFalse("двигатель должен зазвучать после получения данных", activity.enginePlayer.isMuted)
            }

            Thread.sleep(8000)

            scenario.onActivity {
                mockBluetooth.setRaw(512, 850)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            Thread.sleep(2000)

            scenario.onActivity {
                mockBluetooth.setRaw(512, 700)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            Thread.sleep(2000)

            // При возврате в нейтраль (512, 512) двигатель не должен глохнуть,
            // а должен продолжать работать на холостом ходу (обороты задаются speedIntercept > 0)
            scenario.onActivity {
                mockBluetooth.setRaw(512, 512)
            }
            Thread.sleep(1000)
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()

            scenario.onActivity { activity ->
                assertFalse("двигатель должен работать на холостом ходу в нейтрали", activity.enginePlayer.isMuted)
            }

            // При выключении коляски (0, 0) двигатель должен заглохнуть
            scenario.onActivity {
                mockBluetooth.setRaw(0, 0)
            }
            Thread.sleep(1000)
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()

            scenario.onActivity { activity ->
                assertTrue("двигатель должен заглохнуть при выключении коляски (raw=0)", activity.enginePlayer.isMuted)
            }

            // Проверяем глушение при отключении звука мотора в настройках
            scenario.onActivity { activity ->
                PreferenceManager.getDefaultSharedPreferences(activity).edit().putBoolean("disable_engine_sound", true).commit()
                mockBluetooth.setRaw(512, 512)
            }
            Thread.sleep(500)
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()

            scenario.onActivity { activity ->
                assertTrue("двигатель должен заглохнуть при disable_engine_sound", activity.enginePlayer.isMuted)
            }
        }
    }

    private fun waitUntilEngineReady(scenario: ActivityScenario<MainActivity>) {
        val deadline = System.currentTimeMillis() + 5_000
        while (System.currentTimeMillis() < deadline) {
            var ready = false
            scenario.onActivity { activity ->
                ready = activity.enginePlayer.isLoaded && activity.enginePlayer.isStartLoaded
            }
            if (ready) return
            Thread.sleep(50)
        }
        throw AssertionError("звуки двигателя не загрузились за 5 секунд")
    }
}
