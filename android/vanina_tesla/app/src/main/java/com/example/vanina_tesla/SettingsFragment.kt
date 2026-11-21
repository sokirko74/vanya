package com.example.vanina_tesla

import android.content.Intent
import android.os.Bundle
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.PreferenceManager

class SettingsFragment : PreferenceFragmentCompat() {
    override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
        setPreferencesFromResource(R.xml.preferences, rootKey)

        findPreference<Preference>("pref_open_calibration")?.setOnPreferenceClickListener {
            startActivity(Intent(requireContext(), CalibrationActivity::class.java))
            true
        }
    }

    override fun onResume() {
        super.onResume()
        updateCalibrationStatus()
    }

    private fun updateCalibrationStatus() {
        val prefs = PreferenceManager.getDefaultSharedPreferences(requireContext())
        val calib = JoystickCalibration.loadFromPrefs(prefs)
        findPreference<Preference>("pref_calibration_status")?.summary = if (calib.isCalibrated) {
            "Центр: (${calib.neutralX}, ${calib.neutralY})\n" +
            "Вперед (${calib.forward.axis}): [${calib.forward.neutralEdge} .. ${calib.forward.maxEdge}]\n" +
            "Вправо (${calib.right.axis}): [${calib.right.neutralEdge} .. ${calib.right.maxEdge}]\n" +
            "Назад (${calib.backward.axis}): [${calib.backward.neutralEdge} .. ${calib.backward.maxEdge}]\n" +
            "Влево (${calib.left.axis}): [${calib.left.neutralEdge} .. ${calib.left.maxEdge}]"
        } else {
            "Калибровка не выполнена (значения по умолчанию)"
        }
    }
}