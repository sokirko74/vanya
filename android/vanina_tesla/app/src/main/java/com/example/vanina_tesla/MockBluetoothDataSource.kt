package com.example.vanina_tesla

class MockBluetoothDataSource : BluetoothDataSource {
    private var onData: ((WheelchairData) -> Unit)? = null
    private var onLog: ((String) -> Unit)? = null

    @Volatile
    var lastData: WheelchairData = WheelchairData(
        distance1 = 1000,
        distance2 = 1000,
        speed1 = 0,
        speed2 = 0
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
                speed1 = data.speed1,
                speed2 = data.speed2,
                rawX = data.rawX,
                rawY = data.rawY
            )
        )
    }

    fun setSpeed1(value: Int) {
        emit(lastData.copy(speed1 = value))
    }

    fun setRaw(rawX: Int, rawY: Int) {
        emit(lastData.copy(rawX = rawX, rawY = rawY))
    }
}
