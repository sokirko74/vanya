package com.example.vanina_tesla

interface BluetoothDataSource {
    fun startListening(onData: (WheelchairData) -> Unit, onLog: (String) -> Unit)
    fun connect()
    fun stopListening()
}
