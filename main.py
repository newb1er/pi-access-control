from gpiozero import CPUTemperature

from src.cloud import Cloud4RpiConfig, Cloud4RpiVariable, Cloud
from src.access_control import AccessController
from src.card_reader import CardReader

# set up Cloud4Rpi config
# ------------- START LINE --------------------
access_controller = AccessController.get_instance()
reader = CardReader.get_instance()
cpu = CPUTemperature(threshold=10.0)

# Card Reader Pause Toggle
Cloud4RpiConfig.add_var(
    Cloud4RpiVariable('Card Reader Pause', 'bool',
                      reader, 'pause', default=False)()
)

# invalid access
Cloud4RpiConfig.add_var(
    Cloud4RpiVariable('invalid access', 'numeric',
                      access_controller, 'invalid_access_count', immutable=False)()
)

Cloud4RpiConfig.add_var(
    Cloud4RpiVariable('access granted (hour)', 'numeric',
                      access_controller, 'access_granted_hour', immutable=False)()
)

Cloud4RpiConfig.add_var(
    Cloud4RpiVariable('access granted (today)', 'numeric',
                      access_controller, 'access_granted_today', immutable=False)()
)

Cloud4RpiConfig.add_var(
    Cloud4RpiVariable('CPU Temp', 'numeric' if cpu else 'string',
                      cpu, 'temperature', immutable=False)()
)
# --------------- END LINE --------------------


def main():
    cloud = Cloud.get_instance()

    reader.start()
    cloud.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        cloud.kill = True
        cloud.join()
        reader.stop()


if __name__ == '__main__':
    main()
