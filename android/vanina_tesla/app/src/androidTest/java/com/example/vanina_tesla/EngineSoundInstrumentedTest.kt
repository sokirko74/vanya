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
    fun engineSoundsWhenSpeed1IncreasesAndStallsWhenZero() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            waitUntilEngineReady(scenario)

            scenario.onActivity { activity ->
                assertTrue("двигатель должен молчать при старте", activity.enginePlayer.isMuted)
            }

            Thread.sleep(2000)

            log("mockBluetooth.setSpeed1")
            scenario.onActivity {
                mockBluetooth.setSpeed1(256)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()

            scenario.onActivity { activity ->
                assertFalse("двигатель должен зазвучать после speed1 > 0", activity.enginePlayer.isMuted)
            }

            Thread.sleep(8000)

            scenario.onActivity {
                mockBluetooth.setSpeed1(512)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            Thread.sleep(2000)

            scenario.onActivity {
                mockBluetooth.setSpeed1(256)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            Thread.sleep(2000)


            scenario.onActivity {
                mockBluetooth.setSpeed1(0)
            }
            Thread.sleep(1000)
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()

            scenario.onActivity { activity ->
                assertTrue("двигатель должен заглохнуть при speed1 = 0", activity.enginePlayer.isMuted)
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
