package com.example.vanina_tesla

class MockBluetoothDataSource : BluetoothDataSource {
    private var onData: ((WheelchairData) -> Unit)? = null
    private var onLog: ((String) -> Unit)? = null

    @Volatile
    var lastData: WheelchairData = WheelchairData(
        distance1 = 1000,
        distance2 = 1000,
        rawX = 512,
        rawY = 512
    )
        private set

    override fun startListening(onData: (WheelchairData) -> Unit, onLog: (String) -> Unit) {
        this.onData = onData
        this.onLog = onLog
        onLog("Mock Bluetooth готов")
    }

    override fun connect() {
        onLog?.invoke("Mock Bluetooth: подключение не требуется")
    }

    override fun stopListening() {
        onData = null
        onLog = null
    }

    fun emit(data: WheelchairData) {
        lastData = data
        onData?.invoke(
            WheelchairData(
                distance1 = data.distance1,
                distance2 = data.distance2,
                rawX = data.rawX,
                rawY = data.rawY
            )
        )
    }

    fun setRaw(rawX: Int, rawY: Int) {
        emit(lastData.copy(rawX = rawX, rawY = rawY))
    }
}
